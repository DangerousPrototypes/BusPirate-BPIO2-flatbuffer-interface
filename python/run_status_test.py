import sys
import os
import flatbuffers

# Ensure repo root is on path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pybpio.bpio_client import BPIOClient
import tooling.bpio.StatusResponse as StatusResponse
import tooling.bpio.ResponsePacket as ResponsePacket
import tooling.bpio.ResponsePacketContents as ResponsePacketContents


def build_fake_status_response():
    b = flatbuffers.Builder(1024)

    # Strings
    git_hash = b.CreateString("deadbeef")
    fw_date = b.CreateString("2026-01-30")
    mode_current = b.CreateString("testmode")

    # modes_available vector
    mode1 = b.CreateString("mode1")
    mode2 = b.CreateString("mode2")
    StatusResponse.StatusResponseStartModesAvailableVector(b, 2)
    b.PrependUOffsetTRelative(mode2)
    b.PrependUOffsetTRelative(mode1)
    modes_vec = b.EndVector()

    # ADC vector (empty for this test)
    # Build the StatusResponse table
    StatusResponse.StatusResponseStart(b)
    StatusResponse.StatusResponseAddVersionFlatbuffersMajor(b, 2)
    StatusResponse.StatusResponseAddVersionFlatbuffersMinor(b, 0)
    StatusResponse.StatusResponseAddVersionFirmwareMajor(b, 1)
    StatusResponse.StatusResponseAddVersionFirmwareMinor(b, 0)
    StatusResponse.StatusResponseAddVersionFirmwareGitHash(b, git_hash)
    StatusResponse.StatusResponseAddVersionFirmwareDate(b, fw_date)
    StatusResponse.StatusResponseAddModesAvailable(b, modes_vec)
    StatusResponse.StatusResponseAddModeCurrent(b, mode_current)
    status_off = StatusResponse.StatusResponseEnd(b)

    # Wrap in ResponsePacket union
    ResponsePacket.ResponsePacketStart(b)
    ResponsePacket.ResponsePacketAddContentsType(b, ResponsePacketContents.ResponsePacketContents.StatusResponse)
    ResponsePacket.ResponsePacketAddContents(b, status_off)
    resp_off = ResponsePacket.ResponsePacketEnd(b)
    b.Finish(resp_off)
    return bytes(b.Output())


def main():
    resp_bytes = build_fake_status_response()

    def fake_send_and_receive(self, data):
        print("fake_send_and_receive called; returning crafted StatusResponse bytes")
        return resp_bytes

    # Create BPIOClient instance without calling __init__ to avoid opening serial
    client = object.__new__(BPIOClient)
    client.version_flatbuffers_major = 2
    client.minimum_version_flatbuffers_minor = 0
    client.debug = True
    client.serial_port = None
    # Attach the fake sender
    client.send_and_receive = fake_send_and_receive.__get__(client, BPIOClient)

    # Call status_request with no kwargs (request all)
    status = client.status_request()
    print('\nStatus dict (no kwargs):')
    for k, v in status.items():
        print(f"  {k}: {v}")

    # Call status_request requesting only version and io
    status2 = client.status_request(version=True, io=True)
    print('\nStatus dict (version+io):')
    for k, v in status2.items():
        print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
