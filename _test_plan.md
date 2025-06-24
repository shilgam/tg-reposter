## Plan Item: Add Automated Tests for Telegram Reposter

### Goal
Create comprehensive test coverage for the file-driven repost workflow, focusing on behavior verification without implementation coupling.

### Core Test Scenarios

#### 1. **Channel Type Compatibility Tests**
- ✅ **Private source → Public destination** (main regression scenario we fixed)
- ✅ **Public source → Public destination**
- ✅ **Private source → Private destination** (secondary regression we fixed)
- ✅ **Public source → Private destination**

#### 2. **Channel ID Format Handling Tests** ⭐ *NEW - Critical Finding*
- ✅ **Full private channel ID**: `-1002763892937` → stays as integer
- ✅ **Short private channel ID**: `2763892937` → normalized to `-1002763892937` integer
- ✅ **Public channel username**: `antalia_sales` → stays as string
- ✅ **Public channel with @**: `@antalia_sales` → processed correctly
- ❌ **Invalid private channel ID**: Wrong format, too short/long

#### 3. **URL Parsing Tests**
- ✅ **Standard public channel URLs**: `https://t.me/channel_name/123`
- ✅ **Private channel URLs**: `https://t.me/c/1234567890/123` → correctly extracts `-1001234567890`
- ✅ **URL parsing accuracy**: Verify parsed channel ID matches expected format/type
- ❌ **Invalid URLs**: Malformed, missing parts, wrong domains
- ❌ **Empty/whitespace lines** in input file

#### 4. **Data Type Consistency Tests** ⭐ *NEW - Root Cause Coverage*
- ✅ **Private channel type verification**: Ensure private channels become integers before Telethon calls
- ✅ **Public channel type verification**: Ensure public channels remain strings
- ✅ **Source vs destination consistency**: Both follow same type conversion rules
- ❌ **Type conversion edge cases**: Very large numbers, special characters

#### 5. **File I/O Workflow Tests**
- ✅ **Single message repost**: Input file with 1 URL → Output file with 1 URL
- ✅ **Multiple message repost**: Input file with N URLs → Output file with N URLs
- ✅ **Atomic file writing**: Output file only appears when operation completes
- ✅ **Output URL format verification**: Generated URLs match expected pattern
- ❌ **Missing input file**: Graceful error handling
- ❌ **Partial failures**: Some messages succeed, others fail → partial output file

#### 6. **Error Handling & Entity Resolution Tests** ⭐ *UPDATED*
- ❌ **Non-existent source channel**: Clear error message, continues with other URLs
- ❌ **Non-existent destination channel**: Fails early, no partial processing
- ❌ **Non-existent message ID**: Clear error message, continues with other URLs
- ❌ **Permission denied**: Handles auth errors gracefully
- ❌ **Entity resolution fallback**: Test `get_entity()` → `get_input_entity()` fallback chain

#### 7. **End-to-End Integration Test**
- ✅ **Complete workflow**: Real input file → CLI command → Verify output file content matches expected URLs
- ✅ **Cross-platform consistency**: Same behavior on different destination formats

### Test Implementation Notes

**Mock Strategy:**
- Mock Telethon client calls (`get_messages`, `send_message`, `get_entity`, `get_input_entity`)
- Use real file I/O to test file handling logic
- **Test data type handling**: Verify integers vs strings are passed to mocked Telethon calls
- Mock only external API calls, not internal logic

**Test Data:**
- Use consistent test channel IDs: private (`-1002763892937`), public (`test_channel`)
- Test both short (`2763892937`) and full (`-1002763892937`) private channel formats
- Create reusable test input files with mixed channel types
- Verify output URLs match expected format for each channel type

**Critical Test Assertions** ⭐ *NEW*
- **Type assertions**: `assert isinstance(channel_id, int)` for private channels
- **Value assertions**: `assert channel_id == -1002763892937` after normalization
- **URL format assertions**: Output URLs match expected Telegram URL patterns

**Success Criteria:**
- All ✅ scenarios pass
- All ❌ scenarios fail gracefully with clear error messages
- **Data type regression prevention**: Tests catch string vs integer issues
- Tests run in <30 seconds
- No coupling to internal function names or implementation details

### Key Insights from Bugfix ⭐ *NEW SECTION*
1. **Telethon expects specific data types**: Private channels must be integers, public channels can be strings
2. **URL parsing changes data flow**: File-driven workflow introduced string processing that affected type handling
3. **Consistent conversion is critical**: Both source and destination need same type normalization logic
4. **Multiple private channel formats exist**: Short IDs need normalization to full format

This enhanced test suite now covers the **root cause** (data type handling) and **specific regression** (private channel support) we discovered, ensuring future changes won't break private channel functionality.