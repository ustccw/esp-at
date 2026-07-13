如何实现 Bluetooth LE OTA 升级
==========================================

:link_to_translation:`en:[English]`

本文档介绍 ESP-AT 中 Bluetooth LE OTA 升级，分为两部分：

- :ref:`ble-ota-usage`：如何通过 AT 命令和示例 APP 完成升级。
- :ref:`ble-ota-principle`：GATT 服务、对端操作顺序、命令包与固件包格式等协议说明，供自行实现 APP 或主机端时参考。

ESP-AT Bluetooth LE OTA 基于乐鑫 BLE OTA 方案。使用 :ref:`AT+BLEOTA <cmd-BLEOTA>` 初始化 Bluetooth LE OTA 后，设备会开启广播，等待对端 APP 连接，通过 Bluetooth LE 接收固件，校验通过后自动重启。

.. contents::
   :local:
   :depth: 2

.. _ble-ota-usage:

Bluetooth LE OTA 用法
---------------------

概述
^^^^^

Bluetooth LE OTA 无需 Wi-Fi 网络即可升级固件。手机或主机 APP 通过 Bluetooth LE 连接 ESP 设备，按扇区传输新固件，设备将固件写入 Flash，直至升级完成。

典型应用场景：

- 设备没有 Wi-Fi 连接，或升级时 Wi-Fi 不可用。
- 希望通过手机 APP 在本地完成固件升级。
- 除 :ref:`AT+CIUPDATE <cmd-UPDATE>`、:ref:`AT+USEROTA <cmd-USEROTA>`、:ref:`AT+WEBSERVER <cmd-WEBSERVER>` 等网络 OTA 命令外，还需要基于 Bluetooth LE 的 FOTA 通道。

如需了解基于网络的 OTA，请参考 :doc:`How_to_implement_OTA_update`。

准备工作
^^^^^^^^^

.. important::

   默认 AT 固件未使能 Bluetooth LE OTA。如需使用该功能，请自行 :doc:`编译 ESP-AT 工程 <How_to_clone_project_and_compile_it>`，在配置工程时完成以下两项，然后重新编译并烧录固件：

   1. 启用 ``Component config`` > ``AT`` > ``AT ble ota command support``
   2. 同步调整 MTU，建议设置为 ``512``：``Component config`` > ``Bluetooth`` > ``NimBLE Options`` > ``Preferred MTU size in octets``

使用 ESP-AT 进行 Bluetooth LE OTA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

请按以下步骤完成一次典型的 Bluetooth LE OTA 升级。完整命令说明请参考 :ref:`AT+BLEOTANAME <cmd-BLEOTANAME>` 和 :ref:`AT+BLEOTA <cmd-BLEOTA>`。

1. （可选）设置 Bluetooth LE OTA 设备名称。最大长度为 29 字节，默认名称为 ``ESP-C919``。

   命令：

   .. code-block:: none

       AT+BLEOTANAME="NAME"

   响应：

   .. code-block:: none

       OK

2. 初始化 Bluetooth LE OTA。初始化成功后，设备会自动开启广播。

   命令：

   .. code-block:: none

       AT+BLEOTA=1

   响应：

   .. code-block:: none

       OK

3. 在手机上打开示例 APP，连接设备并开始固件升级。详见下方 `示例 APP`_。

4. 固件传输完成并校验通过后，设备会自动重启。

.. note::

   - 如需设置设备名称，请在执行 ``AT+BLEOTA=1`` 前先运行 :ref:`AT+BLEOTANAME <cmd-BLEOTANAME>`。
   - ``AT+BLEOTA=0`` 用于反初始化 Bluetooth LE OTA。
   - 升级过程中请尽量让手机靠近设备，避免因 Bluetooth LE 链路较弱导致传输失败。

示例 APP
^^^^^^^^^

你可以从以下地址获取乐鑫 Bluetooth LE OTA 示例 APP：

- Android：`ESP BLE OTA Android APP <https://github.com/EspressifApps/esp-ble-ota-android/releases/tag/rc>`_
- iOS：`ESP BLE OTA iOS APP <https://github.com/EspressifApps/esp-ble-ota-ios>`_

安装 APP 后，需要将用于升级的固件文件（如 ``app.bin``）手动放到 APP 对应目录下，APP 才能在升级时选择该文件：

- **Android**：将 APK 安装到手机后，先进入一次 APP（会自动创建目录），然后将固件文件放到 ``Android/data/com.espressif.bleota.android/files/BLE-OTA``
- **iOS**：将 iPhone 连接到电脑，通过 Finder (macOS) 或 Apple Devices / iTunes (Windows) 打开该手机，进入 ``文件`` > ``ESP-BLEOTA`` （或 ``esp-ble-ota``），将固件文件拖入该 App 目录

完成上述准备后：

1. 打开手机蓝牙。
2. 打开 APP，扫描附近设备。
3. 连接到执行 ``AT+BLEOTA=1`` 后正在广播的设备。
4. 选择固件文件并开始升级。
5. 等待传输完成。设备校验固件后会自动重启。

若你需要自行实现手机 APP 或主机端，请继续阅读下方 :ref:`ble-ota-principle`。

.. _ble-ota-principle:

Bluetooth LE OTA 原理
---------------------

本节说明 Bluetooth LE OTA 的 GATT 服务、对端操作顺序以及数据包格式，供自行实现对端 APP 时参考。

服务定义
^^^^^^^^^

Bluetooth LE OTA Profile 包含两个服务：

- **DIS Service** (UUID ``0x180A``)：显示软件和硬件版本信息。
- **OTA Service** (UUID ``0x8018``)：用于 OTA 升级，包含 4 个特征值，如下表所示。

.. list-table::
   :header-rows: 1
   :widths: 25 15 25 35

   * - 特征值
     - UUID
     - 属性
     - 说明
   * - RECV_FW_CHAR
     - 0x8020
     - Write, Notify
     - 接收固件数据，并回复 ACK
   * - PROGRESS_BAR_CHAR
     - 0x8021
     - Read, Notify
     - 读取或上报升级进度
   * - COMMAND_CHAR
     - 0x8022
     - Write, Notify
     - 发送 OTA 命令，并回复 ACK
   * - CUSTOMER_CHAR
     - 0x8023
     - Write, Notify
     - 收发用户自定义数据

开始 OTA 前，对端设备必须：

1. 使能所有通过 ACK 回复的特征值的 Indication（向 CCC 写入 ``0x0002``）。
2. 发送“开始 OTA”命令，并在命令 Payload 中携带整个固件的长度。

设备每累计接收 4 KB 数据写一次 Flash。最后不足 4 KB 的扇区，在完整固件接收并校验通过后结束传输。

OTA 操作顺序
^^^^^^^^^^^^^

手机或主机 APP 连接设备后，请按以下顺序操作。**先使能全部 Indication (CCC)，再发送开始 OTA 命令。** 否则设备不会接收固件数据。

.. list-table::
   :header-rows: 1
   :widths: 10 35 55

   * - 步骤
     - 对端设备操作
     - 说明
   * - 1
     - 使能所有通过 ACK 回复的特征值的 Indication
     - 向 RECV_FW_CHAR、COMMAND_CHAR、PROGRESS_BAR_CHAR、CUSTOMER_CHAR 的 CCC 写入 ``0x02 0x00`` （小端，即 ``0x0002``），以开启 Indication。按 BLE CCC 定义，``0x0001`` 使能 Notification，``0x0002`` 使能 Indication。设备通过 Indication 回复 ACK。
   * - 2
     - 下发“开始 OTA”命令
     - 向 COMMAND_CHAR 写入命令包。Command ID ``0x0001`` 表示开始 OTA。Payload 的 Byte 2~5 携带固件总长度。等待设备通过 COMMAND_CHAR Indication 回复 ``0x0003``，且 Byte 4~5 为 ``0x0000`` （接受）后，再进入下一步。
   * - 3
     - 按扇区发送固件数据
     - 使用 Write Without Response 向 RECV_FW_CHAR 写入固件包。每个扇区固定 4 KB。``Sector_Index`` 从 0 递增且不可跳跃。每个扇区发送完成后，需等待成功 ACK，再发送下一扇区。
   * - 4
     - （可选）下发“结束 OTA”命令
     - 固件数据全部发送完成后，可向 COMMAND_CHAR 写入 Command ID ``0x0002`` 以结束 OTA。

简要流程：

**连接 -> 使能 Indication -> 开始 OTA（携带固件长度）-> 按扇区发送固件（每扇区等待 ACK）-> （可选）结束 OTA -> 设备校验固件并重启**

命令包格式
^^^^^^^^^^^

COMMAND_CHAR 使用如下包格式：

.. list-table::
   :header-rows: 1
   :widths: 20 25 30 25

   * - 字段
     - Command_ID
     - PayLoad
     - CRC16
   * - 字节
     - Byte 0 ~ 1
     - Byte 2 ~ 17
     - Byte 18 ~ 19

Command_ID 定义如下：

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Command_ID
     - 含义
     - Payload 说明
   * - 0x0001
     - 开始 OTA
     - Byte 2~5：固件长度（小端）。其余字节置 0。CRC16 对 Byte 0~17 计算。
   * - 0x0002
     - 结束 OTA
     - Payload 全部置 0。CRC16 对 Byte 0~17 计算。
   * - 0x0003
     - 命令包回复
     - Byte 2~3：被回复的 Command_ID。Byte 4~5：``0x0000`` 表示接受，``0x0001`` 表示拒绝。其余字节置 0。

固件数据包格式
^^^^^^^^^^^^^^^

客户端按如下格式向 RECV_FW_CHAR 发送固件包：

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 30

   * - 字段
     - Sector_Index
     - Packet_Seq
     - PayLoad
   * - 字节
     - Byte 0 ~ 1
     - Byte 2
     - Byte 3 ~ (MTU_size - 4)

- **Sector_Index**：扇区号，从 0 递增，不可跳跃。必须发满当前扇区的 4 KB 后才能开始下一扇区，否则设备会立即回复错误 ACK 并要求重传。
- **Packet_Seq**：包序号。``0xFF`` 表示该扇区的最后一包。此时 Payload 最后 2 字节为整个 4 KB 扇区的 CRC16。
- **PayLoad**：固件有效载荷。

回复包与命令包同为 20 字节，未使用字节置 0。CRC16 对 Byte 0~17 计算。

.. list-table::
   :header-rows: 1
   :widths: 18 18 18 18 14 14

   * - 字段
     - Sector_Index
     - ACK_Status
     - Expected_Sector_Index
     - Reserved
     - CRC16
   * - 字节
     - Byte 0 ~ 1
     - Byte 2 ~ 3
     - Byte 4 ~ 5
     - Byte 6 ~ 17
     - Byte 18 ~ 19

ACK_Status 定义如下：

- ``0x0000``：成功
- ``0x0001``：CRC 错误
- ``0x0002``：Sector_Index 错误；Byte 4~5（``Expected_Sector_Index``）表示期望的 Sector_Index
- ``0x0003``：Payload 长度错误

进度条信息
^^^^^^^^^^^

若传输中断或包序号错乱，客户端可主动读取 PROGRESS_BAR_CHAR，并从期望偏移继续传输。

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - 字节
     - 含义
   * - Byte 0 ~ 3
     - ``recv_total_length``
   * - Byte 4 ~ 7
     - ``total_fw_length``
   * - Byte 8 ~ 9
     - CRC16

参考
----------

- Bluetooth LE OTA AT 命令：:ref:`AT+BLEOTANAME <cmd-BLEOTANAME>` 和 :ref:`AT+BLEOTA <cmd-BLEOTA>`
- 网络 OTA 指南：:doc:`How_to_implement_OTA_update`
