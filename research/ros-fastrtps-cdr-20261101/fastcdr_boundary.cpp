// Isolated Fast-CDR v2.2.x cursor/end invariant probe.
// Returns success only when the baseline and negative controls are reproduced.
#include <fastcdr/Cdr.h>
#include <fastcdr/FastBuffer.h>
#include <fastcdr/exceptions/Exception.h>
#include <iostream>

static bool check(const char* name, unsigned char last, bool expected_jump)
{
    char payload[4] = {0, 0, 0, static_cast<char>(last)};
    eprosima::fastcdr::FastBuffer buffer(payload, sizeof(payload));
    eprosima::fastcdr::Cdr cdr(
      buffer, eprosima::fastcdr::Cdr::DEFAULT_ENDIAN);
    try
    {
        cdr.read_encapsulation();
        // There are zero payload bytes; jumping one byte must be impossible.
        // An options value of 1/2 in v2.2.8 moves end_ behind the cursor.
        bool jumped = cdr.jump(1);
        std::cout << name << ": jump_one=" << jumped
                  << " expected=" << expected_jump << std::endl;
        return jumped == expected_jump;
    }
    catch (const eprosima::fastcdr::exception::Exception& e)
    {
        std::cout << name << ": exception=" << e.what() << std::endl;
        return false;
    }
}

int main()
{
    bool ok = true;
    ok &= check("zero_options", 0, false);
    ok &= check("one_byte_padding", 1, true);
    ok &= check("two_byte_padding", 2, true);
    return ok ? 0 : 1;
}
