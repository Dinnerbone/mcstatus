from unittest import TestCase

from mcstatus.bedrock_status import BedrockServerStatus, BedrockStatusResponse

class TestBedrockServerPinger(TestCase):
    def setUp(self):  # Not needed?
        pass

    def test_parse_response(self):
        data = b'\x1c\x00\x00\x00\x00\x00\x00\x00\x004GT\x00\xb8\x83D\xde\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx\x00wMCPE;\xc2\xa7r\xc2\xa74G\xc2\xa7r\xc2\xa76a\xc2\xa7r\xc2\xa7ey\xc2\xa7r\xc2\xa72B\xc2\xa7r\xc2\xa71o\xc2\xa7r\xc2\xa79w\xc2\xa7r\xc2\xa7ds\xc2\xa7r\xc2\xa74e\xc2\xa7r\xc2\xa76r;422;;1;69;3767071975391053022;;Default;1;19132;-1;'
        parsed = BedrockServerStatus.parse_response(data, 1)

        self.assertIsInstance(parsed, BedrockStatusResponse)

        self.assertIn('gamemode', parsed.__dict__)
        self.assertIn('latency', parsed.__dict__)
        self.assertIn('map', parsed.__dict__)
        self.assertIn('motd', parsed.__dict__)
        self.assertIn('players_max', parsed.__dict__)
        self.assertIn('players_online', parsed.__dict__)
        self.assertIn('version', parsed.__dict__)
        self.assertIn('brand', parsed.version.__dict__)
        self.assertIn('protocol', parsed.version.__dict__)
