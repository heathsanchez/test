// Local diagnostic probe only; not part of an upstream change.
// Verify endpoint matching after a TypeLookup timeout, keeping an incompatible
// same-name type distinct from a genuinely identical type.

#include <fastdds/LibrarySettings.hpp>
#include <fastdds/dds/domain/DomainParticipant.hpp>
#include <fastdds/dds/domain/DomainParticipantFactory.hpp>
#include <fastdds/dds/publisher/DataWriter.hpp>
#include <fastdds/dds/publisher/Publisher.hpp>
#include <fastdds/dds/publisher/qos/DataWriterQos.hpp>
#include <fastdds/dds/subscriber/DataReader.hpp>
#include <fastdds/dds/subscriber/Subscriber.hpp>
#include <fastdds/dds/subscriber/qos/DataReaderQos.hpp>
#include <fastdds/dds/topic/TypeSupport.hpp>
#include <fastdds/dds/xtypes/dynamic_types/DynamicPubSubType.hpp>
#include <fastdds/dds/xtypes/dynamic_types/DynamicTypeBuilder.hpp>
#include <fastdds/dds/xtypes/dynamic_types/DynamicTypeBuilderFactory.hpp>
#include <fastdds/dds/xtypes/dynamic_types/MemberDescriptor.hpp>
#include <fastdds/dds/xtypes/type_representation/ITypeObjectRegistry.hpp>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <thread>

using namespace eprosima::fastdds::dds;

int main(int argc, char** argv)
{
    if (argc != 7)
    {
        std::cerr << "Usage: probe publisher|subscriber int|bool flow_bytes timeout_ms domain hold_ms\n";
        return 2;
    }

    const std::string role = argv[1];
    const std::string field_kind = argv[2];
    const uint32_t flow_bytes = static_cast<uint32_t>(std::stoul(argv[3]));
    const uint32_t timeout_ms = static_cast<uint32_t>(std::stoul(argv[4]));
    const uint32_t domain = static_cast<uint32_t>(std::stoul(argv[5]));
    const int hold_ms = std::stoi(argv[6]);

    if ((role != "publisher" && role != "subscriber") ||
            (field_kind != "int" && field_kind != "bool"))
    {
        return 2;
    }

    eprosima::fastdds::LibrarySettings settings;
    settings.intraprocess_delivery = eprosima::fastdds::INTRAPROCESS_OFF;
    DomainParticipantFactory::get_instance()->set_library_settings(settings);

    auto participant_qos = PARTICIPANT_QOS_DEFAULT;
    if (flow_bytes)
    {
        auto controller = std::make_shared<eprosima::fastdds::rtps::FlowControllerDescriptor>();
        controller->name = "TypeIdentityStarvation";
        controller->max_bytes_per_period = flow_bytes;
        controller->period_ms = 100000;
        participant_qos.flow_controllers().push_back(controller);
        participant_qos.wire_protocol().builtin.flow_controller_name = controller->name;
        participant_qos.wire_protocol().builtin.discovery_config.leaseDuration = Duration_t(600, 0);
    }
    if (timeout_ms)
    {
        participant_qos.properties().properties().emplace_back(
            "fastdds.type_lookup_request_timeout_ms", std::to_string(timeout_ms));
    }

    DomainParticipant* participant = DomainParticipantFactory::get_instance()->create_participant(
        domain, participant_qos);
    if (!participant)
    {
        std::cerr << "create_participant failed\n";
        return 3;
    }

    TypeDescriptor::_ref_type type_descriptor {traits<TypeDescriptor>::make_shared()};
    type_descriptor->kind(TK_STRUCTURE);
    type_descriptor->name("Telemetry");
    auto builder = DynamicTypeBuilderFactory::get_instance()->create_type(type_descriptor);
    MemberDescriptor::_ref_type member {traits<MemberDescriptor>::make_shared()};
    member->name("field_0");
    member->type(DynamicTypeBuilderFactory::get_instance()->get_primitive_type(
                field_kind == "int" ? TK_INT32 : TK_BOOLEAN));
    if (!builder || builder->add_member(member) != RETCODE_OK)
    {
        std::cerr << "create_type failed\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 4;
    }

    // The associated TypeObject must exceed the 6 KiB builtin flow-controller
    // budget, as in eProsima's Case 14. A one-field type is too small and can
    // resolve normally despite the restricted controller.
    for (uint32_t i = 1; i <= 320; ++i)
    {
        MemberDescriptor::_ref_type padding {traits<MemberDescriptor>::make_shared()};
        padding->name("padding_" + std::to_string(i));
        padding->type(DynamicTypeBuilderFactory::get_instance()->get_primitive_type(TK_INT32));
        if (builder->add_member(padding) != RETCODE_OK)
        {
            std::cerr << "add_member failed at " << i << "\n";
            participant->delete_contained_entities();
            DomainParticipantFactory::get_instance()->delete_participant(participant);
            return 8;
        }
    }

    TypeSupport type(new DynamicPubSubType(builder->build()));
    if (type.register_type(participant) != RETCODE_OK)
    {
        std::cerr << "register_type failed\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 5;
    }

    xtypes::TypeInformation type_information;
    if (DomainParticipantFactory::get_instance()->type_object_registry().get_type_information(
                type.get()->type_identifiers(), type_information) != RETCODE_OK)
    {
        std::cerr << "registered type has no TypeInformation\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 9;
    }
    const uint32_t type_object_bytes =
            type_information.complete().typeid_with_size().typeobject_serialized_size();
    std::cout << "TYPE_ID_PROBE type_object_bytes=" << type_object_bytes << std::endl;
    if (flow_bytes && type_object_bytes <= flow_bytes)
    {
        std::cerr << "TypeObject is too small to exercise the starvation gate\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 10;
    }

    Topic* topic = participant->create_topic("TelemetryTopic", type.get_type_name(), TOPIC_QOS_DEFAULT);
    if (!topic)
    {
        std::cerr << "create_topic failed\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 6;
    }

    DataWriter* writer = nullptr;
    DataReader* reader = nullptr;
    if (role == "publisher")
    {
        Publisher* publisher = participant->create_publisher(PUBLISHER_QOS_DEFAULT);
        if (publisher)
        {
            auto writer_qos = DATAWRITER_QOS_DEFAULT;
            writer_qos.data_sharing().off();
            writer_qos.reliability().kind = RELIABLE_RELIABILITY_QOS;
            writer_qos.durability().kind = TRANSIENT_LOCAL_DURABILITY_QOS;
            writer = publisher->create_datawriter(topic, writer_qos);
        }
    }
    else
    {
        Subscriber* subscriber = participant->create_subscriber(SUBSCRIBER_QOS_DEFAULT);
        if (subscriber)
        {
            auto reader_qos = DATAREADER_QOS_DEFAULT;
            reader_qos.data_sharing().off();
            reader_qos.reliability().kind = RELIABLE_RELIABILITY_QOS;
            reader_qos.durability().kind = TRANSIENT_LOCAL_DURABILITY_QOS;
            reader = subscriber->create_datareader(topic, reader_qos);
        }
    }
    if (!writer && !reader)
    {
        std::cerr << "create_endpoint failed\n";
        participant->delete_contained_entities();
        DomainParticipantFactory::get_instance()->delete_participant(participant);
        return 7;
    }

    int max_matched = 0;
    const auto until = std::chrono::steady_clock::now() + std::chrono::milliseconds(hold_ms);
    while (std::chrono::steady_clock::now() < until)
    {
        if (writer)
        {
            PublicationMatchedStatus status;
            writer->get_publication_matched_status(status);
            max_matched = std::max(max_matched, static_cast<int>(status.current_count));
        }
        else
        {
            SubscriptionMatchedStatus status;
            reader->get_subscription_matched_status(status);
            max_matched = std::max(max_matched, static_cast<int>(status.current_count));
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::cout << "TYPE_ID_PROBE role=" << role
              << " field=" << field_kind
              << " flow_bytes=" << flow_bytes
              << " max_matched=" << max_matched << std::endl;
    participant->delete_contained_entities();
    DomainParticipantFactory::get_instance()->delete_participant(participant);
    return 0;
}
