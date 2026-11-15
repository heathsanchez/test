#include "rtps/builtin/discovery/endpoint/EDP.h"
#include "rtps/builtin/data/ReaderProxyData.hpp"
#include "rtps/builtin/data/WriterProxyData.hpp"

#include <iostream>

using namespace eprosima::fastdds::rtps;

class MatchingProbe : public EDP
{
public:

    MatchingProbe()
        : EDP(nullptr, nullptr)
    {
    }

    bool initEDP(BuiltinAttributes&) override
    {
        return true;
    }

    void assignRemoteEndpoints(const ParticipantProxyData&, bool) override
    {
    }

    bool remove_reader(RTPSReader*) override
    {
        return true;
    }

    bool remove_writer(RTPSWriter*) override
    {
        return true;
    }

    bool process_reader_proxy_data(RTPSReader*, ReaderProxyData*) override
    {
        return true;
    }

    bool process_writer_proxy_data(RTPSWriter*, WriterProxyData*) override
    {
        return true;
    }
};

int main()
{
    MatchingProbe edp;
    WriterProxyData writer(0, 0);
    ReaderProxyData reader(0, 0);

    writer.topic_name = "TelemetryTopic";
    reader.topic_name = "TelemetryTopic";
    writer.type_name = "Telemetry";
    reader.type_name = "Telemetry";

    EDP::MatchingFailureMask reason;
    eprosima::fastdds::dds::PolicyMask incompatible;

    // Deliberately no TypeInformation on either proxy. Default compatibility
    // policy permits matching based on the equal type names.
    reader.type_consistency.m_force_type_validation = false;
    bool default_matches = edp.valid_matching(&writer, &reader, reason, incompatible);

    // In the same unavailable-TypeInformation state, an explicit strict reader
    // must not match solely by name.
    reader.type_consistency.m_force_type_validation = true;
    bool strict_matches = edp.valid_matching(&writer, &reader, reason, incompatible);

    std::cout << "EDP_POLICY_PROBE default_matches=" << default_matches
              << " strict_matches=" << strict_matches
              << " strict_missing_typeinfo_reason="
              << reason.test(EDP::MatchingFailureMask::different_typeinfo)
              << std::endl;

    return default_matches && !strict_matches &&
           reason.test(EDP::MatchingFailureMask::different_typeinfo) ? 0 : 1;
}
