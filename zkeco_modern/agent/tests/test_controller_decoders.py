from agent.controller_decoders import decode_transaction_rows, decode_user_rows, parse_option_pairs


def test_parse_option_pairs_handles_multi_line_payload():
    raw = "IPAddress=192.168.1.235,TCPPort=14370\r\nHTTPPort=443,FirmVer=AC Ver 4.7.8.3033"

    parsed = parse_option_pairs(raw)

    assert parsed["IPAddress"] == "192.168.1.235"
    assert parsed["TCPPort"] == "14370"
    assert parsed["HTTPPort"] == "443"


def test_decode_user_rows_handles_full_header_even_when_fields_were_narrow():
    raw = (
        "UID,CardNo,Pin,Password,Group,StartTime,EndTime,Name,SuperAuthorize,Disable\r\n"
        "12,123456,93,,7,2000-01-01 00:00:00,2099-12-31 23:59:59,Multi Card,0,0"
    )

    rows = decode_user_rows(raw)

    assert rows == [
        {
            "uid": "12",
            "cardno": "123456",
            "pin": "93",
            "password": "",
            "group": "7",
            "start_time": "2000-01-01 00:00:00",
            "end_time": "2099-12-31 23:59:59",
            "name": "Multi Card",
            "super_authorize": "0",
            "disable": "0",
        }
    ]


def test_decode_transaction_rows_handles_cardno_first_header_payload():
    raw = (
        "Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index\r\n"
        "123456,93,4,1,27,0,840045753,04EEFF11"
    )

    rows = decode_transaction_rows(raw)

    assert rows == [
        {
            "cardno": "123456",
            "pin": "93",
            "verified": "4",
            "door_id": "1",
            "event_type": "27",
            "in_out_state": "0",
            "time_second": "840045753",
            "index": "04EEFF11",
            "source_format": "header-driven",
        }
    ]


def test_decode_transaction_rows_handles_key_value_payload():
    raw = "Cardno=123456\tPin=93\tVerified=4\tDoorID=1\tEventType=27\tInOutState=0\tTime_second=840045753\tIndex=77"

    rows = decode_transaction_rows(raw)

    assert rows == [
        {
            "cardno": "123456",
            "pin": "93",
            "verified": "4",
            "door_id": "1",
            "event_type": "27",
            "in_out_state": "0",
            "time_second": "840045753",
            "index": "77",
            "sitecode": "",
            "source_format": "key-value",
        }
    ]


def test_decode_transaction_rows_handles_card_alias_in_header_payload():
    raw = (
        "Card,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index\r\n"
        "123456,93,4,1,27,0,840045753,77"
    )

    rows = decode_transaction_rows(raw)

    assert rows == [
        {
            "cardno": "123456",
            "pin": "93",
            "verified": "4",
            "door_id": "1",
            "event_type": "27",
            "in_out_state": "0",
            "time_second": "840045753",
            "index": "77",
            "source_format": "header-driven",
        }
    ]


def test_decode_transaction_rows_handles_card_alias_in_key_value_payload():
    raw = "Card=123456\tPin=93\tVerified=4\tDoorID=1\tEventType=27\tInOutState=0\tTime_second=840045753\tIndex=77"

    rows = decode_transaction_rows(raw)

    assert rows == [
        {
            "cardno": "123456",
            "pin": "93",
            "verified": "4",
            "door_id": "1",
            "event_type": "27",
            "in_out_state": "0",
            "time_second": "840045753",
            "index": "77",
            "sitecode": "",
            "source_format": "key-value",
        }
    ]
