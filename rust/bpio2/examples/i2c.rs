//! Read 8 bytes at address 0x10 from a 24-series EEPROM over I2C.
//!
//! This example consists of four main parts, which are common when interacting with
//! the Bus Pirate via BPIO2 to perform a data transfer:
//!
//! 1. Configure the correct mode
//! 2. Check that configuration occurred OK
//! 3. Send a data transfer request
//! 4. Check that the data transfer occurred OK

use std::time::Duration;

use bpio2::{
    ConfigurationRequestBuilder, DataRequestBuilder, ModeConfigurationBuilder, RequestPacket,
    RequestPacketArgs, RequestPacketBuilder, RequestPacketContents, ResponsePacketContents,
};
use flatbuffers::FlatBufferBuilder;

#[allow(unused, unused_mut)]
fn main() {
    let mut serial_port = open_serial_port();

    // The FlatBufferBuilder encodes our types into bytes we can send to the Bus Pirate.
    let mut fbb = FlatBufferBuilder::new();

    // Building flatbuffer types requires `fbb` to be mutably borrowed, so when building the
    // enclosing types we need to have already created their contents.

    // ModeConfiguration lets us set the I2C bus speed, and whether to use clock stretching. We'll
    // use the builder type because we only need to set some of the fields, and set the speed to
    // 400 kHz, and disable clock-stretching.
    let mut mode_config = ModeConfigurationBuilder::new(&mut fbb);
    mode_config.add_speed(400_000);
    mode_config.add_clock_stretch(false);
    // When we're done setting fields, we need to finish the struct off. This consumes the builder,
    // releases the mutable borrow of `fbb`, and gives us something we can use to include the mode
    // config into our larger request.
    let mode_config = mode_config.finish();

    // To put the Bus Pirate into I2C mode we need to set the mode name as a string.
    let mode_name = fbb.create_string("I2C");

    // We'll construct a configuration request and add our previously-created mode name and mode
    // configuration to it.
    let mut configuration_request = ConfigurationRequestBuilder::new(&mut fbb);
    configuration_request.add_mode(mode_name);
    configuration_request.add_mode_configuration(mode_config);
    // Let's enable the PSU at 3.3V and 300mA to power the EEPROM.
    configuration_request.add_psu_enable(true);
    configuration_request.add_psu_set_mv(3_300);
    configuration_request.add_psu_set_ma(300);
    // And enable pull-up resistors on the Bus Pirate so I2C works. (You might not need this if,
    // for example, you're using a breakout board that includes pull-up resistors.)
    configuration_request.add_pullup_enable(true);
    let configuration_request = configuration_request.finish();

    // The configuration request needs to be packaged into a RequestPacket. Alongside the actual
    // request data, we need to say which type of request we're making, and what version of the
    // BPIO2 schema we are using.
    //
    // We need to set all the fields, so we won't use the builder type this time, and create the
    // packet in one go.
    let mut request_packet = RequestPacket::create(
        &mut fbb,
        &RequestPacketArgs {
            version_major: 2,
            version_minor: 0,
            contents_type: RequestPacketContents::ConfigurationRequest,
            // To set the value of a union field, we need to call `as_union_value()` to sort-of
            // erase the concrete type of the value.
            contents: Some(configuration_request.as_union_value()),
        },
    );

    // Now we're finished constructing our request, we instruct `fbb` to make the
    // RequestPacket the root of the flatbuffer it's building.
    fbb.finish_minimal(request_packet);
    let flatbuffer_bytes = fbb.finished_data();

    // BPIO2 uses consistent-overhead byte stuffing (COBS) so the start and end of
    // each packet are clear. We need to COBS-encode the flatbuffer bytes before
    // sending them to the Bus Pirate.
    let mut cobs_encoded = cobs::encode_vec(flatbuffer_bytes);
    // And ensure the packet is terminated with the 0x00 sentinel value.
    cobs_encoded.push(0x00);

    // Now we can send the packet
    serial_port
        .write_all(&cobs_encoded)
        .expect("Failed to write configuration packet.");

    // And receive the COBS-encoded response. The `cobs` crate allows us to easily
    // decode the stream of bytes as we read them from the serial port.
    let mut decode_buffer = [0u8; 256];
    let mut decoder = cobs::CobsDecoder::new(&mut decode_buffer);
    let decoded_bytes = loop {
        let mut per_read_buffer = [0u8; 128];
        let bytes_read = serial_port
            .read(&mut per_read_buffer)
            .expect("Failed to read from the serial port.");
        let decode_state = decoder
            .push(&per_read_buffer[..bytes_read])
            .expect("COBS-decoding error.");
        if let Some(decode_report) = decode_state {
            // Successfully decoded a COBS-encoded message.
            break &decoder.dest()[..decode_report.parsed_size()];
        }
    };

    // Now we'll turn the COBS-decoded bytes into a meaningful ResponsePacket.
    let response = bpio2::root_as_response_packet(decoded_bytes)
        .expect("Failed to parse bytes as response packet after configuration request.");

    // Check that there wasn't an error with our request
    match response.contents_type() {
        ResponsePacketContents::ErrorResponse => {
            // Something went wrong with our request.
            let contents = response.contents_as_error_response().unwrap();
            panic!(
                "Received error response from BusPirate: {:?}",
                contents.error()
            );
        }
        ResponsePacketContents::ConfigurationResponse => {
            let contents = response.contents_as_configuration_response().unwrap();
            // Check there was no configuration-specific error
            if let Some(error_message) = contents.error() {
                panic!("Configuration response error: {:?}", error_message);
            }
        }
        other => {
            panic!("Unexpected response contents type {:?}", other);
        }
    }

    // The Bus Pirate is now in I2C mode, ready to carry out our transaction.
    // To re-use the existing FlatBufferBuilder, we need to reset it.
    fbb.reset();

    // To read from address 0x10 of the EEPROM, we need to write the *8-bit* device address (0x50)
    // and the starting byte address. These bytes are supplied in a vector. You will typically have
    // to provide the item type (u8) when creating flatbuffer vectors.
    //
    // In I2C mode, the address is always supplied in the `data_write` vector, even for
    // transactions that are just reads. The Bus Pirate will correctly set the read/not write bit
    // in the address.
    let data_write = fbb.create_vector::<u8>(&[0xA0, 0x10]);
    // Creating a vector is easy if you already have a &[u8]. If you don't, you can push each byte
    // onto the vector separately, for instance if you have the address and data bytes separately.
    // Note these are *pushed* like a stack: last-in, first-out.
    //
    // fbb.start_vector::<u8>(2);
    // fbb.push(0x10); // EEPROM starting byte address
    // fbb.push(0xA0); // EEPROM I2C write address.
    // let write_data = fbb.end_vector::<u8>(2);

    // We can create the data request now we have the data_write vector.
    //
    // Because we are writing and reading, the Bus Pirate will perform an I2C Write-Read:
    // Start, write address, data bytes, Repeated-Start, read address, read n bytes, Stop
    let mut data_request = DataRequestBuilder::new(&mut fbb);
    data_request.add_start_main(true);
    data_request.add_data_write(data_write);
    data_request.add_bytes_read(8); // Read 8 bytes.
    data_request.add_stop_main(true);
    let data_request = data_request.finish();

    // Package the data request in a request packet as before
    let mut request_packet = RequestPacketBuilder::new(&mut fbb);
    request_packet.add_version_major(2);
    request_packet.add_version_minor(0);
    request_packet.add_contents_type(RequestPacketContents::DataRequest);
    request_packet.add_contents(data_request.as_union_value());
    let request_packet = request_packet.finish();

    // And finish off and COBS-encode as before.
    fbb.finish_minimal(request_packet);
    let flatbuffer_bytes = fbb.finished_data();
    let mut cobs_encoded = cobs::encode_vec(flatbuffer_bytes);
    cobs_encoded.push(0x00);

    serial_port
        .write_all(&cobs_encoded)
        .expect("Failed to write configuration packet.");

    // Read and decode the response as before.
    let mut decode_buffer = [0u8; 256];
    let mut decoder = cobs::CobsDecoder::new(&mut decode_buffer);
    let decoded_bytes = loop {
        let mut per_read_buffer = [0u8; 128];
        let bytes_read = serial_port
            .read(&mut per_read_buffer)
            .expect("Failed to read from the serial port.");
        let decode_state = decoder
            .push(&per_read_buffer[..bytes_read])
            .expect("COBS-decoding error.");
        if let Some(decode_report) = decode_state {
            // Successfully decoded a COBS-encoded message.
            break &decoder.dest()[..decode_report.parsed_size()];
        }
    };

    let response = bpio2::root_as_response_packet(decoded_bytes)
        .expect("Failed to parse bytes as response packet after data request.");
    let bytes_read_from_eeprom = match response.contents_type() {
        ResponsePacketContents::ErrorResponse => {
            // Something went wrong with our request.
            let contents = response.contents_as_error_response().unwrap();
            panic!(
                "Received error response from BusPirate: {:?}",
                contents.error()
            );
        }
        ResponsePacketContents::DataResponse => {
            let contents = response.contents_as_data_response().unwrap();
            // Check there was no error
            if let Some(error_message) = contents.error() {
                panic!("Configuration response error: {:?}", error_message);
            }
            // Get the read bytes from the response.
            contents.data_read().unwrap().bytes()
        }
        other => {
            panic!("Unexpected response contents type {:?}", other);
        }
    };

    // Finally, print the 8 bytes read from address 0x10 of the EEPROM.
    println!("{:X?}", bytes_read_from_eeprom);
}

fn open_serial_port() -> Box<dyn serialport::SerialPort> {
    let Some(serial_port_path) = std::env::args().nth(1) else {
        eprintln!("Provide the path to the serial port as the first argument.");
        std::process::exit(-1);
    };
    let Ok(port) = serialport::new(serial_port_path, 115_200)
        .timeout(Duration::from_millis(500))
        .open()
    else {
        eprintln!("Failed to open serial port.");
        std::process::exit(-2);
    };
    port
}
