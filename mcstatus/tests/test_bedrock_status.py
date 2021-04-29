from mcstatus.bedrock_status import BedrockServerStatus, BedrockStatusResponse


def test_bedrock_response_contains_expected_fields():
    data = b"\x1c\x00\x00\x00\x00\x00\x00\x00\x004GT\x00\xb8\x83D\xde\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx\x00wMCPE;\xc2\xa7r\xc2\xa74G\xc2\xa7r\xc2\xa76a\xc2\xa7r\xc2\xa7ey\xc2\xa7r\xc2\xa72B\xc2\xa7r\xc2\xa71o\xc2\xa7r\xc2\xa79w\xc2\xa7r\xc2\xa7ds\xc2\xa7r\xc2\xa74e\xc2\xa7r\xc2\xa76r;422;;1;69;3767071975391053022;;Default;1;19132;-1;"
    parsed = BedrockServerStatus.parse_response(data, 1)
    assert isinstance(parsed, BedrockStatusResponse)
    assert "gamemode" in parsed.__dict__
    assert "latency" in parsed.__dict__
    assert "map" in parsed.__dict__
    assert "motd" in parsed.__dict__
    assert "players_max" in parsed.__dict__
    assert "players_online" in parsed.__dict__
    assert "version" in parsed.__dict__
    assert "brand" in parsed.version.__dict__
    assert "protocol" in parsed.version.__dict__
