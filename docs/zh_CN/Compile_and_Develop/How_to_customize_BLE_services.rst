如何自定义低功耗蓝牙服务
========================================

:link_to_translation:`en:[English]`

本文档介绍了如何利用 ESP-AT 提供的低功耗蓝牙服务源文件在 {IDF_TARGET_NAME} 设备上自定义低功耗蓝牙服务。

.. contents::
   :local:
   :depth: 2

低功耗蓝牙服务被定义为 GATT 结构的多元数组，该数组至少包含一个属性类型 (attribute type) 为 0x2800 的首要服务 (primary service)。每个服务总是由一个服务定义和几个特征组成。每个特征总是由一个值和可选的描述符组成。更多相关信息请参阅 `《蓝牙核心规范》 <https://www.bluetooth.com/specifications/specs/core-specification-4-2>`_ 中的 Generic Attribute Profile (GATT) 一节。

所有支持低功耗蓝牙的芯片共用同一份 ``gatts_data.csv`` 格式。下文说明在 {IDF_TARGET_NAME} 上各字段是否生效。

.. _factory-gatts-intro:

低功耗蓝牙服务源文件介绍
---------------------------------

低功耗蓝牙服务源文件是 ESP-AT 工程创建低功耗蓝牙服务所依据的文件，文件位于 :component_file:`customized_partitions/raw_data/ble_data/gatts_data.csv`，内容如下表所示。

.. list-table::
   :header-rows: 1

   * - index
     - uuid_len
     - uuid
     - perm
     - val_max_len
     - val_cur_len
     - value
   * - 0
     - 16
     - 0x2800
     - 0x01
     - 2
     - 2
     - A002
   * - 1
     - 16
     - 0x2803
     - 0x01
     - 1
     - 1
     - 02
   * - 2
     - 16
     - 0xC300
     - 0x01
     - 1
     - 1
     - 30
   * - 3
     - 16
     - 0x2901
     - 0x11
     - 1
     - 1
     - 30
   * - ...
     - ...
     - ...
     - ...
     - ...
     - ...
     - ...

以下内容是对上表的说明。

- ``perm`` 字段描述属性权限。当某行的 ``perm`` 生效时（见下文规则），它在 ESP-AT 工程中的定义如下所示：

  .. code-block:: c

    /* relate to BTA_GATT_PERM_xxx in bta/bta_gatt_api.h */
    /**
    * @brief Attribute permissions
    */
    #define ESP_GATT_PERM_READ (1 << 0) /* bit 0 - 0x0001 */ /* relate to BTA_GATT_PERM_READ in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_READ_ENCRYPTED (1 << 1) /* bit 1 - 0x0002 */ /* relate to BTA_GATT_PERM_READ_ENCRYPTED in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_READ_ENC_MITM (1 << 2) /* bit 2 - 0x0004 */ /* relate to BTA_GATT_PERM_READ_ENC_MITM in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_WRITE (1 << 4) /* bit 4 - 0x0010 */ /* relate to BTA_GATT_PERM_WRITE in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_WRITE_ENCRYPTED (1 << 5) /* bit 5 - 0x0020 */ /* relate to BTA_GATT_PERM_WRITE_ENCRYPTED in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_WRITE_ENC_MITM (1 << 6) /* bit 6 - 0x0040 */ /* relate to BTA_GATT_PERM_WRITE_ENC_MITM in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_WRITE_SIGNED (1 << 7) /* bit 7 - 0x0080 */ /* relate to BTA_GATT_PERM_WRITE_SIGNED in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_WRITE_SIGNED_MITM (1 << 8) /* bit 8 - 0x0100 */ /* relate to BTA_GATT_PERM_WRITE_SIGNED_MITM in bta/bta_gatt_api.h */
    #define ESP_GATT_PERM_READ_AUTHORIZATION (1 << 9) /* bit 9 - 0x0200 */
    #define ESP_GATT_PERM_WRITE_AUTHORIZATION (1 << 10) /* bit 10 - 0x0400 */

- 上表第一行是服务定义。该行的属性类型为 ``0x2800`` （首要服务），其 ``value`` ``A002`` 表示 16 位服务 UUID ``0xA002``。
- 第二行是特征声明。UUID ``0x2803`` 表示该行是特征声明。

  - ``value``：表示下一行特征值属性的特征属性 (characteristic properties)。该字段为 1 字节（8 位），每一位表示是否支持对应属性，``1`` 表示支持，``0`` 表示不支持。

  .. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

     在 {IDF_TARGET_NAME} 上，ESP-AT 会在内部自动转换该属性值，无需处理其中的差异。

  例如，``value`` 为 ``02`` 表示下一行特征具备 READ 属性。

  .. list-table::
     :header-rows: 1
     :widths: 20 100

     * - 位
       - 特征属性
     * - 0
       - BROADCAST
     * - 1
       - READ
     * - 2
       - WRITE WITHOUT RESPONSE
     * - 3
       - WRITE
     * - 4
       - NOTIFY
     * - 5
       - INDICATE
     * - 6
       - AUTHENTICATION SIGNED WRITES
     * - 7
       - EXTENDED PROPERTIES

- 第三行定义该特征的特征值属性。该行的 ``uuid`` 是特征 UUID，``value`` 是特征的初始值。
- 第四行定义了特征的描述符（可选）。
- ``value`` 字段可以缺省。若缺省（留空），ESP-AT 在初始化时会将该属性自动填充为全 ``0``。例如，默认表中特征 ``0xC301`` 一行的 ``value`` 为空，则该特征会初始化为全 ``0``。

字段规则
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. only:: esp32 or esp32c3

   - 对于 ``0x2803`` 行，``perm`` 与 ``value`` 均生效：``perm`` 是声明属性自身的权限（一般为 ``0x01``，可读），``value`` 是下一行特征的属性。
   - 对于特征值行，``perm`` 生效，且不得与上一行 ``0x2803`` 的特征属性冲突。特征属性向客户端声明该特征支持哪些操作；``perm`` 决定协议栈是否真正允许这些操作。例如，若属性声明为只读，但特征值行的 ``perm`` 却是只写，客户端按声明去读时会失败。

     常见对应关系如下（若需要安全访问，可改用对应的加密、签名等权限变体）：

     .. list-table::
        :header-rows: 1
        :widths: 35 65

        * - 若特征属性包含
          - 特征值行的 ``perm`` 至少应包含
        * - READ
          - READ（即 ``0x01``），或相关的加密、授权读变体
        * - WRITE
          - WRITE（即 ``0x10``），或相关的加密、授权、签名写变体
        * - WRITE WITHOUT RESPONSE
          - WRITE（即 ``0x10``），或相关的加密、授权、签名写变体
        * - NOTIFY 或 INDICATE
          - 特征值行通常为 READ；需自行添加 CCCD（即 ``0x2902``），其 ``perm`` 一般为 READ | WRITE（即 ``0x11``）

     特征属性可以组合。例如 ``0A`` （即 READ | WRITE）应与特征值行 ``perm`` ``0x11`` （即 READ | WRITE）配对。

   - 若特征支持 NOTIFY 或 INDICATE，需在表中自行添加 ``0x2902`` 行。其他描述符（如 ``0x2901``）也会按表添加，且各描述符行的 ``perm`` 生效。

.. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

   - 对于 ``0x2803`` 行，只看 ``value`` （下一行特征的属性）。本行的 ``perm`` 会被忽略、不生效。
   - 对于特征值行，本行的 ``perm`` 会被忽略、不生效。若未提供下文所述的第 8 个可选字段，特征能力只来自上一行 ``0x2803`` 的 ``value`` （特征属性）。
   - 若特征属性包含 NOTIFY 或 INDICATE，会自动添加 CCCD（``0x2902``）。``gatts_data.csv`` 中的 ``0x2902`` 行会被跳过、不处理（为兼容 CSV 仍可保留这些行；在 {IDF_TARGET_NAME} 上它们只是不生效）。
   - 其他描述符（如 ``0x2901``）仍会被添加。若未提供下文所述的第 8 个可选字段，这些描述符行以本行的 ``perm`` 为准。

   **可选第 8 字段**

   在 {IDF_TARGET_NAME} 上，特征值行和描述符行还可以在 ``value`` 之后追加一个可选字段。前缀 ``0x`` / ``0X`` 可写可不写。服务定义行（``0x2800``）、特征声明行（``0x2803``）等其他行即使填写该字段，也不会生效。

   1. 特征值行：第 8 字段为 32 位十六进制串，表示该特征的完整属性标志。若填写了该字段，则上一行 ``0x2803`` 的 ``value`` （特征属性）会被忽略、不生效，以本字段为准。

      例如，原来的：

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30

      也可以写成：

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30,0x00020000

      或：

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30,00020000

      该字段定义如下（可按位或组合）：

      .. code-block:: c

        #define BLE_GATT_CHR_F_BROADCAST 0x00000001
        #define BLE_GATT_CHR_F_READ 0x00000002
        #define BLE_GATT_CHR_F_WRITE_NO_RSP 0x00000004
        #define BLE_GATT_CHR_F_WRITE 0x00000008
        #define BLE_GATT_CHR_F_NOTIFY 0x00000010
        #define BLE_GATT_CHR_F_INDICATE 0x00000020
        #define BLE_GATT_CHR_F_AUTH_SIGN_WRITE 0x00000040
        #define BLE_GATT_CHR_F_RELIABLE_WRITE 0x00000080
        #define BLE_GATT_CHR_F_AUX_WRITE 0x00000100
        #define BLE_GATT_CHR_F_READ_ENC 0x00000200
        #define BLE_GATT_CHR_F_READ_AUTHEN 0x00000400
        #define BLE_GATT_CHR_F_READ_AUTHOR 0x00000800
        #define BLE_GATT_CHR_F_WRITE_ENC 0x00001000
        #define BLE_GATT_CHR_F_WRITE_AUTHEN 0x00002000
        #define BLE_GATT_CHR_F_WRITE_AUTHOR 0x00004000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_ENC 0x00008000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_AUTHEN 0x00010000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_AUTHOR 0x00020000

   2. 描述符行：第 8 字段为 8 位十六进制串，表示该描述符的权限。若填写了该字段，则本行的 ``perm`` 会被忽略、不生效，以本字段为准。

      例如，原来的：

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30

      也可以写成：

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30,0x80

      或：

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30,80

      该字段定义如下（可按位或组合）：

      .. code-block:: c

        #define BLE_ATT_F_READ 0x01
        #define BLE_ATT_F_WRITE 0x02
        #define BLE_ATT_F_READ_ENC 0x04
        #define BLE_ATT_F_READ_AUTHEN 0x08
        #define BLE_ATT_F_READ_AUTHOR 0x10
        #define BLE_ATT_F_WRITE_ENC 0x20
        #define BLE_ATT_F_WRITE_AUTHEN 0x40
        #define BLE_ATT_F_WRITE_AUTHOR 0x80

有关 UUID 的更多信息请参考 `蓝牙技术联盟分配符 <https://www.bluetooth.com/specifications/assigned-numbers/>`_。

如果直接在 {IDF_TARGET_NAME} 设备上使用默认源文件，不做任何修改，并建立低功耗蓝牙连接，那么在客户端查询服务器服务后，会得到如下结果。

.. figure:: ../../_static/compile_and_develop/ble_default_service.png
    :scale: 100 %
    :align: center
    :alt: ESP-AT 默认低功耗蓝牙服务

编译时自定义低功耗蓝牙服务
-------------------------------

请根据以下步骤自定义低功耗蓝牙服务。

.. contents::
   :local:
   :depth: 1

修改低功耗蓝牙服务源文件
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

可定义多个服务，例如，若要定义三个服务（``Server_A``、``Server_B`` 和 ``Server_C``），则需要将这三个服务按顺序排列。由于定义每个服务的操作大同小异，这里我们以定义一个服务为例，其他服务你可以按照此例进行定义。

1. 添加服务定义。

   本例定义了一个值为 0xFF01 的主要服务。

   .. list-table::
      :header-rows: 1

      * - index
        - uuid_len
        - uuid
        - perm
        - val_max_len
        - val_cur_len
        - value
      * - 31
        - 16
        - 0x2800
        - 0x01
        - 2
        - 2
        - FF01

2. 添加特征说明和特征值。

   本例定义了一个 UUID 为 0xC300 的可读可写特征，并将其值设置为 0x30。

   .. only:: esp32 or esp32c3

      声明行 ``perm`` 为 ``0x01``。特征值行 ``perm`` 为 ``0x11`` （需与 READ | WRITE 属性对应）。

   .. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

      声明行 ``perm`` 与特征值行 ``perm`` 会被忽略、不生效。

   .. list-table::
      :header-rows: 1

      * - index
        - uuid_len
        - uuid
        - perm
        - val_max_len
        - val_cur_len
        - value
      * - 32
        - 16
        - 0x2803
        - 0x01
        - 1
        - 1
        - 0A
      * - 33
        - 16
        - 0xC300
        - 0x11
        - 1
        - 1
        - 30

3. 添加特征描述符（可选）。

   步骤 2 中的特征属性为 ``0A`` （表示 READ | WRITE），**不需要** CCCD。下方内容是针对支持 NOTIFY 或 INDICATE 的特征的 **独立可选示例**，与上面的 ``0A`` 示例无关。若需要 NOTIFY，请相应设置 ``0x2803`` 的属性（例如 ``1A`` 表示 READ | WRITE | NOTIFY）。

   .. only:: esp32 or esp32c3

      若特征支持 NOTIFY 或 INDICATE，需自行添加客户端特征配置（``0x2902``）。下表示例将 ``value`` 设为 ``0000`` （通知和指示关闭）。

      CCCD 行示例：

      .. list-table::
         :header-rows: 1

         * - index
           - uuid_len
           - uuid
           - perm
           - val_max_len
           - val_cur_len
           - value
         * - 34
           - 16
           - 0x2902
           - 0x11
           - 2
           - 2
           - 0000

      完成以上步骤后，自定义的低功耗蓝牙服务可如下定义。下表将步骤 1–2 的服务与特征，与步骤 3 的可选 CCCD 示例合并展示。若仅使用 ``0A`` （READ | WRITE）特征，可省略 ``0x2902`` 行。

      .. list-table::
         :header-rows: 1

         * - index
           - uuid_len
           - uuid
           - perm
           - val_max_len
           - val_cur_len
           - value
         * - 31
           - 16
           - 0x2800
           - 0x01
           - 2
           - 2
           - FF01
         * - 32
           - 16
           - 0x2803
           - 0x01
           - 1
           - 1
           - 0A
         * - 33
           - 16
           - 0xC300
           - 0x11
           - 1
           - 1
           - 30
         * - 34
           - 16
           - 0x2902
           - 0x11
           - 2
           - 2
           - 0000

   .. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

      若属性包含 NOTIFY 或 INDICATE，CCCD 会自动添加。无需再添加 ``0x2902`` 行；若 CSV 中已有该行，会被跳过、不生效。其他非 ``0x2902`` 的描述符仍会添加，且该行的 ``perm`` 生效。

      完成以上步骤后，自定义的低功耗蓝牙服务可如下定义（``0A`` 的 READ | WRITE 示例；无需 ``0x2902`` 行）：

      .. list-table::
         :header-rows: 1

         * - index
           - uuid_len
           - uuid
           - perm
           - val_max_len
           - val_cur_len
           - value
         * - 31
           - 16
           - 0x2800
           - 0x01
           - 2
           - 2
           - FF01
         * - 32
           - 16
           - 0x2803
           - 0x01
           - 1
           - 1
           - 0A
         * - 33
           - 16
           - 0xC300
           - 0x11
           - 1
           - 1
           - 30

请根据自己的需求修改 GATTS 配置，然后生成 ``mfg_nvs.bin`` 文件。

生成 mfg_nvs.bin 文件
^^^^^^^^^^^^^^^^^^^^^^^^^^

请参考 :ref:`mfg-nvs-generate` 文档生成带有低功耗蓝牙的服务配置的 ``mfg_nvs.bin``。

下载 mfg_nvs.bin 文件
^^^^^^^^^^^^^^^^^^^^^^^^^^

请参考 :ref:`mfg-nvs-download` 文档。

下载完成后，重新建立低功耗蓝牙连接，在客户端查询的服务器服务如下所示。

.. figure:: ../../_static/compile_and_develop/ble_customize_service.png
    :scale: 100 %
    :align: center
    :alt: ESP-AT 自定义低功耗蓝牙服务
