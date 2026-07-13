How to Implement Bluetooth LE OTA Upgrade
==========================================

:link_to_translation:`zh_CN:[中文]`

This document introduces Bluetooth LE OTA upgrade in ESP-AT and is organized into two parts:

- :ref:`ble-ota-usage-en`: How to complete an upgrade with AT commands and the sample APP.
- :ref:`ble-ota-principle-en`: GATT services, peer-device operation sequence, and command or firmware packet formats for implementing your own APP or host.

ESP-AT Bluetooth LE OTA is based on the Espressif BLE OTA solution. After you initialize Bluetooth LE OTA with :ref:`AT+BLEOTA <cmd-BLEOTA>`, the device starts advertising, waits for the peer APP to connect, receives the firmware over Bluetooth LE, verifies it, and then restarts automatically.

.. contents::
   :local:
   :depth: 2

.. _ble-ota-usage-en:

Bluetooth LE OTA Usage
----------------------

Overview
^^^^^^^^

Bluetooth LE OTA upgrades firmware without a Wi-Fi network. A phone or host APP connects to the ESP device over Bluetooth LE, transfers the new firmware sector by sector, and the device writes the firmware to flash until the upgrade is complete.

Typical use cases:

- The device has no Wi-Fi connection, or Wi-Fi is unavailable during upgrade.
- You want to upgrade firmware locally through a phone APP.
- You need a Bluetooth LE-based FOTA channel in addition to network OTA commands such as :ref:`AT+CIUPDATE <cmd-UPDATE>`, :ref:`AT+USEROTA <cmd-USEROTA>`, and :ref:`AT+WEBSERVER <cmd-WEBSERVER>`.

For network-based OTA, please refer to :doc:`How_to_implement_OTA_update`.

Preparation
^^^^^^^^^^^

.. important::

   The default AT firmware does not enable Bluetooth LE OTA. To use this feature, :doc:`compile the ESP-AT project <How_to_clone_project_and_compile_it>` yourself, complete the following two configuration items, then rebuild and flash the firmware:

   1. Enable ``Component config`` > ``AT`` > ``AT ble ota command support``
   2. Update the MTU at the same time. The recommended value is ``512``: ``Component config`` > ``Bluetooth`` > ``NimBLE Options`` > ``Preferred MTU size in octets``

Use Bluetooth LE OTA with ESP-AT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Follow the steps below for a typical Bluetooth LE OTA upgrade. For full command details, please refer to :ref:`AT+BLEOTANAME <cmd-BLEOTANAME>` and :ref:`AT+BLEOTA <cmd-BLEOTA>`.

1. (Optional) Set the Bluetooth LE OTA device name. The maximum length is 29 bytes. The default name is ``ESP-C919``.

   Command:

   .. code-block:: none

       AT+BLEOTANAME="NAME"

   Response:

   .. code-block:: none

       OK

2. Initialize Bluetooth LE OTA. After initialization succeeds, the device automatically starts advertising.

   Command:

   .. code-block:: none

       AT+BLEOTA=1

   Response:

   .. code-block:: none

       OK

3. Open the sample APP on your phone, connect to the device, and start the firmware upgrade. See `Sample APP`_ below.

4. After the firmware transfer is completed and verification succeeds, the device restarts automatically.

.. note::

   - Set the device name with :ref:`AT+BLEOTANAME <cmd-BLEOTANAME>` before running ``AT+BLEOTA=1``.
   - ``AT+BLEOTA=0`` deinitializes Bluetooth LE OTA.
   - During upgrade, keep the phone close to the device to avoid transfer failure caused by a weak Bluetooth LE link.

Sample APP
^^^^^^^^^^

You can get the Espressif Bluetooth LE OTA sample APP from:

- Android: `ESP BLE OTA Android APP <https://github.com/EspressifApps/esp-ble-ota-android/releases/tag/rc>`_
- iOS: `ESP BLE OTA iOS APP <https://github.com/EspressifApps/esp-ble-ota-ios>`_

After installing the APP, manually place the firmware file used for upgrade (for example, ``app.bin``) into the APP directory so that the APP can select it during upgrade:

- **Android**: After installing the APK, open the APP once (the directory is created automatically), then put the firmware file into ``Android/data/com.espressif.bleota.android/files/BLE-OTA``
- **iOS**: Connect the iPhone to a computer, open the phone in Finder (macOS) or Apple Devices / iTunes (Windows), go to ``Files`` > ``ESP-BLEOTA`` (or ``esp-ble-ota``), and drag the firmware file into the App directory

Then:

1. Turn on Bluetooth on your phone.
2. Open the APP and scan for nearby devices.
3. Connect to the device that is advertising after ``AT+BLEOTA=1``.
4. Select the firmware file and start the upgrade.
5. Wait until the transfer is completed. The device verifies the firmware and restarts automatically.

If you need to implement your own phone APP or host, continue with :ref:`ble-ota-principle-en` below.

.. _ble-ota-principle-en:

Bluetooth LE OTA Principle
--------------------------

This section describes the GATT services, peer-device operation sequence, and packet formats of Bluetooth LE OTA for implementing your own peer APP.

Service Definition
^^^^^^^^^^^^^^^^^^

The Bluetooth LE OTA profile contains two services:

- **DIS Service** (UUID ``0x180A``): displays software and hardware version information.
- **OTA Service** (UUID ``0x8018``): used for OTA upgrade. It contains 4 characteristics, as shown below.

.. list-table::
   :header-rows: 1
   :widths: 25 15 25 35

   * - Characteristic
     - UUID
     - Properties
     - Description
   * - RECV_FW_CHAR
     - 0x8020
     - Write, Notify
     - Receive firmware data and reply with ACK
   * - PROGRESS_BAR_CHAR
     - 0x8021
     - Read, Notify
     - Read or report the upgrade progress
   * - COMMAND_CHAR
     - 0x8022
     - Write, Notify
     - Send OTA commands and reply with ACK
   * - CUSTOMER_CHAR
     - 0x8023
     - Write, Notify
     - Send and receive user-defined data

Before starting OTA, the peer device must:

1. Enable Indication for all characteristics that reply with ACK (write CCC ``0x0002``).
2. Send the "Start OTA" command, and include the total firmware length in the command payload.

The device writes flash once every 4 KB of received data. For the last sector that is smaller than 4 KB, the transfer ends after the complete firmware has been received and verified.

OTA Operation Sequence
^^^^^^^^^^^^^^^^^^^^^^

After the phone or host APP connects to the device, follow this sequence. **Enable all Indications (CCC) first, then send the Start OTA command.** Otherwise, the device will not accept firmware data.

.. list-table::
   :header-rows: 1
   :widths: 10 35 55

   * - Step
     - Peer Device Action
     - Description
   * - 1
     - Enable Indication for all characteristics that reply with ACK
     - Write ``0x02 0x00`` (little-endian, namely ``0x0002``) to the CCC of RECV_FW_CHAR, COMMAND_CHAR, PROGRESS_BAR_CHAR, and CUSTOMER_CHAR to enable Indication. Per the BLE CCC definition, ``0x0001`` enables Notification and ``0x0002`` enables Indication. The device replies with ACK through Indication.
   * - 2
     - Send the Start OTA command
     - Write a command packet to COMMAND_CHAR. Command ID ``0x0001`` means Start OTA. Payload bytes 2 to 5 carry the total firmware length. Wait for the device to reply ``0x0003`` through COMMAND_CHAR Indication, with bytes 4 to 5 equal to ``0x0000`` (accepted), and then continue.
   * - 3
     - Send firmware data by sector
     - Write firmware packets to RECV_FW_CHAR with Write Without Response. Each sector is 4 KB. ``Sector_Index`` starts from 0 and must increase continuously. After each sector, wait for a success ACK before sending the next sector.
   * - 4
     - (Optional) Send the Stop OTA command
     - After all firmware data has been sent, you may write Command ID ``0x0002`` to COMMAND_CHAR to stop OTA.

Simplified flow:

**Connect -> Enable Indication -> Start OTA (with firmware length) -> Send firmware by sector (wait for ACK per sector) -> (Optional) Stop OTA -> Device verifies firmware and restarts**

Command Packet Format
^^^^^^^^^^^^^^^^^^^^^

COMMAND_CHAR uses the following packet format:

.. list-table::
   :header-rows: 1
   :widths: 20 25 30 25

   * - Field
     - Command_ID
     - PayLoad
     - CRC16
   * - Bytes
     - Byte 0 ~ 1
     - Byte 2 ~ 17
     - Byte 18 ~ 19

Command_ID definitions:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Command_ID
     - Meaning
     - Payload Description
   * - 0x0001
     - Start OTA
     - Bytes 2 to 5: firmware length (little-endian). Other bytes are set to 0. CRC16 is calculated over bytes 0 to 17.
   * - 0x0002
     - Stop OTA
     - All payload bytes are set to 0. CRC16 is calculated over bytes 0 to 17.
   * - 0x0003
     - Command response
     - Bytes 2 to 3: the Command_ID being responded to. Bytes 4 to 5: ``0x0000`` means accept, ``0x0001`` means reject. Other bytes are set to 0.

Firmware Packet Format
^^^^^^^^^^^^^^^^^^^^^^

The client sends firmware packets to RECV_FW_CHAR in the following format:

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 30

   * - Field
     - Sector_Index
     - Packet_Seq
     - PayLoad
   * - Bytes
     - Byte 0 ~ 1
     - Byte 2
     - Byte 3 ~ (MTU_size - 4)

- **Sector_Index**: sector number starting from 0. It must increase continuously. You must finish sending 4 KB for the current sector before starting the next one; otherwise, the device replies with an error ACK and requests retransmission.
- **Packet_Seq**: packet sequence number. ``0xFF`` means this is the last packet of the sector. In that case, the last 2 bytes of Payload are the CRC16 of the entire 4 KB sector.
- **PayLoad**: firmware payload.

The reply packet is also 20 bytes, the same as the command packet. Unused bytes are set to 0. CRC16 is calculated over bytes 0 to 17.

.. list-table::
   :header-rows: 1
   :widths: 18 18 18 18 14 14

   * - Field
     - Sector_Index
     - ACK_Status
     - Expected_Sector_Index
     - Reserved
     - CRC16
   * - Bytes
     - Byte 0 ~ 1
     - Byte 2 ~ 3
     - Byte 4 ~ 5
     - Byte 6 ~ 17
     - Byte 18 ~ 19

ACK_Status definitions:

- ``0x0000``: Success
- ``0x0001``: CRC error
- ``0x0002``: Sector_Index error; bytes 4 to 5 (``Expected_Sector_Index``) indicate the expected Sector_Index
- ``0x0003``: Payload length error

Progress Bar Information
^^^^^^^^^^^^^^^^^^^^^^^^

If the transfer is interrupted or packet sequence becomes disordered, the client can actively read PROGRESS_BAR_CHAR and continue from the expected offset.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Bytes
     - Meaning
   * - Byte 0 ~ 3
     - ``recv_total_length``
   * - Byte 4 ~ 7
     - ``total_fw_length``
   * - Byte 8 ~ 9
     - CRC16

References
----------

- Bluetooth LE OTA AT commands: :ref:`AT+BLEOTANAME <cmd-BLEOTANAME>` and :ref:`AT+BLEOTA <cmd-BLEOTA>`
- Network OTA guide: :doc:`How_to_implement_OTA_update`
