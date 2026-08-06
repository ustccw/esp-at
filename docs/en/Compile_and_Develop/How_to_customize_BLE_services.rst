How to Customize Bluetooth® LE Services
========================================

:link_to_translation:`zh_CN:[中文]`

This document describes how to customize Bluetooth LE services on your {IDF_TARGET_NAME} with the Bluetooth LE service source file provided by ESP-AT.

.. contents::
   :local:
   :depth: 2

The Bluetooth LE services are defined as a multivariate array of GATT structures, and the array contains at least one primary service whose attribute type is defined as 0x2800. Each service always consists of a service definition and several characteristics. Each characteristic always consists of a value and optional descriptors. Please refer to Part Generic Attribute Profile (GATT) of `Bluetooth Core Specification <https://www.bluetooth.com/specifications/specs/core-specification-4-2>`_ for more information.

ESP-AT uses the same ``gatts_data.csv`` format on all chips that support Bluetooth LE. The rules below describe which fields take effect on {IDF_TARGET_NAME}.

.. _factory-gatts-intro:

Bluetooth LE Service Source File
--------------------------------

The ESP-AT project creates Bluetooth LE services based on its Bluetooth LE service source file. It is located in :component_file:`customized_partitions/raw_data/ble_data/gatts_data.csv`. The table below shows the default source file.

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

Below are descriptions of the table above.

- ``perm`` describes attribute permissions. When a row's ``perm`` takes effect (see the rules below), its definition in the ESP-AT project is as follows:

  .. code-block:: c

    /* relate to BTA_GATT_PERM_xxx in bta/bta_gatt_api.h */
    /**
    * @brief Attribute permissions
    */
    #define    ESP_GATT_PERM_READ                  (1 << 0)   /* bit 0 -  0x0001 */    /* relate to BTA_GATT_PERM_READ in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_READ_ENCRYPTED        (1 << 1)   /* bit 1 -  0x0002 */    /* relate to BTA_GATT_PERM_READ_ENCRYPTED in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_READ_ENC_MITM         (1 << 2)   /* bit 2 -  0x0004 */    /* relate to BTA_GATT_PERM_READ_ENC_MITM in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_WRITE                 (1 << 4)   /* bit 4 -  0x0010 */    /* relate to BTA_GATT_PERM_WRITE in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_WRITE_ENCRYPTED       (1 << 5)   /* bit 5 -  0x0020 */    /* relate to BTA_GATT_PERM_WRITE_ENCRYPTED in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_WRITE_ENC_MITM        (1 << 6)   /* bit 6 -  0x0040 */    /* relate to BTA_GATT_PERM_WRITE_ENC_MITM in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_WRITE_SIGNED          (1 << 7)   /* bit 7 -  0x0080 */    /* relate to BTA_GATT_PERM_WRITE_SIGNED in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_WRITE_SIGNED_MITM     (1 << 8)   /* bit 8 -  0x0100 */    /* relate to BTA_GATT_PERM_WRITE_SIGNED_MITM in bta/bta_gatt_api.h */
    #define    ESP_GATT_PERM_READ_AUTHORIZATION    (1 << 9)   /* bit 9 -  0x0200 */
    #define    ESP_GATT_PERM_WRITE_AUTHORIZATION   (1 << 10)  /* bit 10 - 0x0400 */

- The first line of the table is the service definition. Its attribute type is ``0x2800`` (primary service), and its ``value`` ``A002`` is the 16-bit service UUID ``0xA002``.
- The second line is the characteristic declaration. UUID ``0x2803`` identifies this row as a characteristic declaration.

  - ``value``: characteristic properties of the **next** characteristic value attribute (the following row). It is one byte (8 bits). Each bit indicates whether a property is supported (``1``) or not (``0``).

  .. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

     On {IDF_TARGET_NAME}, ESP-AT translates this property value internally; you do not need to handle the difference.

  For example, ``value`` ``02`` means the following characteristic has the READ property.

  .. list-table::
     :header-rows: 1
     :widths: 20 100

     * - Bit
       - Characteristic Property
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

- The third line defines the characteristic value attribute of that characteristic. The ``uuid`` of this line is the characteristic UUID, and ``value`` is the characteristic's initial value.
- The fourth line defines a descriptor of the characteristic (optional).
- The ``value`` field is optional. If it is left empty, ESP-AT fills the attribute with all zeros during initialization. For example, in the default table, the characteristic ``0xC301`` row leaves ``value`` empty, so the characteristic is initialized to all zeros.

Field Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. only:: esp32 or esp32c3

   - For the ``0x2803`` row, both ``perm`` and ``value`` take effect: ``perm`` is the permission of the declaration attribute itself (usually ``0x01``, readable), and ``value`` is the properties of the next characteristic.
   - For the characteristic value row, ``perm`` takes effect. It must not conflict with the properties in the previous ``0x2803`` row. Properties advertise which operations the characteristic supports; ``perm`` controls whether the stack actually allows those operations. If properties claim READ-only but the value-row ``perm`` is WRITE-only, clients will fail when they try to read.

     Typical mapping (encrypted or signed permission variants may be used when security is required):

     .. list-table::
        :header-rows: 1
        :widths: 35 65

        * - If properties include
          - Characteristic value ``perm`` should include at least
        * - READ
          - READ (``0x01``), or a read-related encrypted/authorized variant
        * - WRITE
          - WRITE (``0x10``), or a write-related encrypted/authorized/signed variant
        * - WRITE WITHOUT RESPONSE
          - WRITE (``0x10``), or a write-related encrypted/authorized/signed variant
        * - NOTIFY or INDICATE
          - Usually READ on the characteristic value; you must add the CCCD (``0x2902``) yourself. Its ``perm`` is typically READ | WRITE (``0x11``).

     You can combine properties. For example, ``0A`` (READ | WRITE) should be paired with characteristic value ``perm`` ``0x11`` (READ | WRITE).

   - If the characteristic supports NOTIFY or INDICATE, add a ``0x2902`` row in the table. Other descriptors (such as ``0x2901``) are also added as defined, and each descriptor row's ``perm`` takes effect.

.. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

   - For the ``0x2803`` row, only ``value`` (properties of the next characteristic) takes effect. The ``perm`` of this row is **ignored and does not take effect**.
   - For the characteristic value row, ``perm`` is **ignored and does not take effect**. If the optional 8th field described below is not provided, the characteristic capabilities come only from the ``value`` (properties) of the previous ``0x2803`` row.
   - If the characteristic properties include NOTIFY or INDICATE, the CCCD (``0x2902``) is **added automatically**. Any ``0x2902`` row in ``gatts_data.csv`` is **skipped and not processed** (you may keep such rows for CSV compatibility; they simply do not take effect on {IDF_TARGET_NAME}).
   - Other descriptors (such as ``0x2901``) are still added. If the optional 8th field described below is not provided, ``perm`` of **that descriptor row** takes effect.

   **Optional 8th field**

   On {IDF_TARGET_NAME}, **characteristic value rows** and **descriptor rows** may append an optional field after ``value``. The ``0x`` / ``0X`` prefix is optional. If you add this field on other rows (such as the service definition ``0x2800`` or the characteristic declaration ``0x2803``), it **does not take effect**.

   1. **Characteristic value row**: the 8th field is a **32-bit** hexadecimal string that sets the full characteristic flag. If this field is present, the ``value`` (properties) of the **previous** ``0x2803`` row is **ignored and does not take effect**; this field takes precedence.

      For example, the original row:

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30

      can also be written as:

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30,0x00020000

      or:

      .. code-block:: none

         2,16,0xC300,0x01,1,1,30,00020000

      The field is defined as follows (bits can be combined with OR):

      .. code-block:: c

        #define BLE_GATT_CHR_F_BROADCAST                0x00000001
        #define BLE_GATT_CHR_F_READ                     0x00000002
        #define BLE_GATT_CHR_F_WRITE_NO_RSP             0x00000004
        #define BLE_GATT_CHR_F_WRITE                    0x00000008
        #define BLE_GATT_CHR_F_NOTIFY                   0x00000010
        #define BLE_GATT_CHR_F_INDICATE                 0x00000020
        #define BLE_GATT_CHR_F_AUTH_SIGN_WRITE          0x00000040
        #define BLE_GATT_CHR_F_RELIABLE_WRITE           0x00000080
        #define BLE_GATT_CHR_F_AUX_WRITE                0x00000100
        #define BLE_GATT_CHR_F_READ_ENC                 0x00000200
        #define BLE_GATT_CHR_F_READ_AUTHEN              0x00000400
        #define BLE_GATT_CHR_F_READ_AUTHOR              0x00000800
        #define BLE_GATT_CHR_F_WRITE_ENC                0x00001000
        #define BLE_GATT_CHR_F_WRITE_AUTHEN             0x00002000
        #define BLE_GATT_CHR_F_WRITE_AUTHOR             0x00004000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_ENC      0x00008000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_AUTHEN   0x00010000
        #define BLE_GATT_CHR_F_NOTIFY_INDICATE_AUTHOR   0x00020000

   2. **Descriptor row**: the 8th field is an **8-bit** hexadecimal string that sets the descriptor permission. If this field is present, ``perm`` of **this row** is **ignored and does not take effect**; this field takes precedence.

      For example, the original row:

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30

      can also be written as:

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30,0x80

      or:

      .. code-block:: none

         3,16,0x2901,0x11,1,1,30,80

      The field is defined as follows (bits can be combined with OR):

      .. code-block:: c

        #define BLE_ATT_F_READ             0x01
        #define BLE_ATT_F_WRITE            0x02
        #define BLE_ATT_F_READ_ENC         0x04
        #define BLE_ATT_F_READ_AUTHEN      0x08
        #define BLE_ATT_F_READ_AUTHOR      0x10
        #define BLE_ATT_F_WRITE_ENC        0x20
        #define BLE_ATT_F_WRITE_AUTHEN     0x40
        #define BLE_ATT_F_WRITE_AUTHOR     0x80

For more information about UUID, please refer to `Bluetooth Special Interest Group (SIG) Assigned Numbers <https://www.bluetooth.com/specifications/assigned-numbers/>`_.

If you use the default source file on your {IDF_TARGET_NAME} without any modification and establish a Bluetooth LE connection, you will get the following result after querying the server service on the client side.

.. figure:: ../../_static/compile_and_develop/ble_default_service.png
    :scale: 100 %
    :align: center
    :alt: ESP-AT Default Bluetooth LE Service

Customize Bluetooth LE Services during Compilation
--------------------------------------------------

If you want to customize the Bluetooth LE services, follow the steps below.

.. contents::
   :local:
   :depth: 1

Modify the Bluetooth LE Service Source File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can define more than one service. For example, if you want to define three services (``Server_A``, ``Server_B`` and ``Server_C``), these three services need to be arranged in order. Since the definition of each service is similar, here we define one service as an example, and then you can define others one by one accordingly.

1. Add the service definition.

   In this example, we define a primary service with a value of 0xFF01.

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

2. Add the characteristic declaration and characteristic value.

   In this example, we define a readable and writable characteristic with UUID 0xC300, and set its value to 0x30.

   .. only:: esp32 or esp32c3

      The declaration-row ``perm`` is ``0x01``. The characteristic-value-row ``perm`` is ``0x11`` (required to match READ | WRITE properties).

   .. only:: esp32c2 or esp32c5 or esp32c6 or esp32c61

      The declaration-row ``perm`` and the characteristic-value-row ``perm`` are ignored and do not take effect.

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

3. Add the characteristic descriptor (optional).

   The characteristic in step 2 uses properties ``0A`` (READ | WRITE) and does **not** require a CCCD. The content below is a **separate optional illustration** for characteristics that support NOTIFY or INDICATE; it is not tied to the ``0A`` example above. If you need NOTIFY, set the ``0x2803`` properties accordingly (for example ``1A`` for READ | WRITE | NOTIFY).

   .. only:: esp32 or esp32c3

      If the characteristic supports NOTIFY or INDICATE, add client characteristic configuration (``0x2902``) yourself. The example below sets ``value`` to ``0000`` (notifications and indications disabled).

      Example of a CCCD row:

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

      After the above steps, the customized Bluetooth LE service can be defined as follows. The table combines the service and characteristic from steps 1–2 with the optional CCCD illustration from step 3. For the ``0A`` (READ | WRITE) characteristic alone, omit the ``0x2902`` row.

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

      If properties include NOTIFY or INDICATE, CCCD is added automatically. You do not need to add a ``0x2902`` row; if the row exists in the CSV, it is skipped and does not take effect. Other descriptors (not ``0x2902``) are still added, and that row's ``perm`` takes effect.

      After the above steps, the customized Bluetooth LE service can be defined as follows (the ``0A`` READ | WRITE example; no ``0x2902`` row is needed):

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

Please modify the GATTS configurations according to your own needs and generate ``mfg_nvs.bin`` file.

Generate mfg_nvs.bin
^^^^^^^^^^^^^^^^^^^^^

Please refer to :ref:`mfg-nvs-generate` document to generate the ``mfg_nvs.bin`` file with the Low Energy Bluetooth services.

Download mfg_nvs.bin
^^^^^^^^^^^^^^^^^^^^^

Please refer to :ref:`mfg-nvs-download` document.

After the download is complete, re-establish the Bluetooth LE connection. Query the server service on the client side as follows:

.. figure:: ../../_static/compile_and_develop/ble_customize_service.png
    :scale: 100 %
    :align: center
    :alt: ESP-AT Customized Bluetooth LE Service
