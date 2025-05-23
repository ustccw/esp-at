.. _User-AT:

User AT Commands
=================

:link_to_translation:`zh_CN:[中文]`

-  :ref:`AT+USERRAM <cmd-USERRAM>`: Operate user's free RAM.
-  :ref:`AT+USEROTA <cmd-USEROTA>`: Upgrade the firmware according to the specified URL.
-  :ref:`AT+USERWKMCUCFG <cmd-USERWKMCUCFG>`: Configure how AT wakes up MCU.
-  :ref:`AT+USERMCUSLEEP <cmd-USERMCUSLEEP>`: MCU indicates its sleep state.

.. _cmd-USERRAM:

:ref:`AT+USERRAM <User-AT>`: Operate user's free RAM
------------------------------------------------------

Query Command
^^^^^^^^^^^^^

**Function:**

Query the current available user's RAM size.

**Command:**

::

    AT+USERRAM?

**Response:**

::

    +USERRAM:<size>
    OK

Set Command
^^^^^^^^^^^

**Function:**

Allocate, read, write, erase, and free user's RAM

**Command:**

::

    AT+USERRAM=<operation>,<size>[,<offset>]

**Response:**

::

    +USERRAM:<length>,<data>    // esp-at returns this response only when the operator is ``read``

    OK

Parameters
^^^^^^^^^^

-  **<operation>**:

   -  0: release user's RAM
   -  1: malloc user's RAM
   -  2: write user's RAM
   -  3: read user's RAM
   -  4: clear user's RAM

-  **<size>**: the size to malloc/read/write
-  **<offset>**: the offset to read/write. Default: 0

Notes
^^^^^

-  Please malloc the RAM size before you perform any other operations.
-  If the operator is ``write``, wrap return ``>`` after the write command, then you can send the data that you want to write. The length should be parameter ``<length>``.
-  If the operator is ``read`` and the length is bigger than 1024, ESP-AT will reply multiple times in the same format, each reply can carry up to 1024 bytes of data, and eventually end up with ``\r\nOK\r\n``.

Example
^^^^^^^^

::

    // malloc 1 KB user's RAM
    AT+USERRAM=1,1024

    // write 500 bytes to RAM (offset: 0)
    AT+USERRAM=2,500

    // read 64 bytes from RAM offset 100
    AT+USERRAM=3,64,100

    // free the user's RAM
    AT+USERRAM=0

.. _cmd-USEROTA:

:ref:`AT+USEROTA <User-AT>`: Upgrade the Firmware According to the Specified URL
-----------------------------------------------------------------------------------------------------

ESP-AT upgrades firmware at runtime by downloading the new firmware from a specific URL.

Set Command
^^^^^^^^^^^

**Function:**

Upgrade to the firmware version specified by the URL.

**Command:**

::

    AT+USEROTA=<url len>

**Response:**

::

    OK

    >

This response indicates that AT is ready for receiving URL. You should enter the URL, and when the URL length reaches the ``<url len>`` value, the system returns:

::

    Recv <url len> bytes

After AT outputs the above information, the upgrade process starts. If the upgrade process is complete, the system returns:

::

    OK

If the parameter is wrong or firmware upgrades fails, the system returns:

::

    ERROR

Parameters
^^^^^^^^^^

- **<url len>**: URL length. Maximum: 8192 bytes.

Note
^^^^^

-  You can `Download AT firmware from GitHub Actions <https://docs.espressif.com/projects/esp-at/en/latest/esp32/Compile_and_Develop/How_to_download_the_latest_temporary_version_of_AT_from_github.html>`_, or you can generate OTA firmware from :doc:`Compile ESP-AT Project <../Compile_and_Develop/How_to_clone_project_and_compile_it>` as well.
-  OTA firmware is ``build/esp-at.bin``.
-  The speed of the upgrade depends on the network status.
-  If the upgrade fails due to unfavorable network conditions, AT will return ``ERROR``. Please wait for some time before retrying.
-  Downgrading to an older version is not recommended due to potential compatibility issues and the risk of operational failure. If you still prefer downgrading to an older version, please test and verify the functionality based on your product.
-  After you upgrade the AT firmware, you are suggested to call the command :ref:`AT+RESTORE <cmd-RESTORE>` to restore the factory default settings.
-  ``AT+USEROTA`` only supports ``HTTP``.
-  After AT outputs the ``>`` character, the special characters in the URL does not need to be escaped through the escape character, and it does not need to end with a new line (CR-LF).
-  Please refer to :doc:`../Compile_and_Develop/How_to_implement_OTA_update` for more OTA commands.

Example
^^^^^^^^

::

    AT+USEROTA=36

    OK

    >
    Recv 36 bytes

    OK

.. _cmd-USERWKMCUCFG:

:ref:`AT+USERWKMCUCFG <User-AT>`: Configure How AT Wakes up MCU
---------------------------------------------------------------

Set Command
^^^^^^^^^^^

**Function:**

This command configures how AT checks whether MCU is in awake state and how to wake it up.

- If MCU is in awake state, AT will directly send the data to it without waking it up.
- If MCU is in sleep state and AT is ready to actively send the data to MCU (the data sent actively is the same as defined in `ESP-AT Message Reports <https://docs.espressif.com/projects/esp-at/en/release-v2.2.0.0_esp8266/AT_Command_Set/index.html#at-messages>`_), AT will first send wake signals to MCU and then send the data. The wake signals will be cleared after MCU wakes up or times out.

**Command:**

::

    AT+USERWKMCUCFG=<enable>,<wake mode>,<wake number>,<wake signal>,<delay time>[,<check mcu awake method>]

**Response:**

::

    OK

Parameters
^^^^^^^^^^

- **<enable>**: Enable or disable wake-up configuration.

  - 0: Disable wake-up configuration
  - 1: Enable wake-up configuration

- **<wake mode>**: Wake mode.

  - 1: GPIO wake-up
  - 2: UART wake-up

- **<wake number>**: It means differently depending on the parameter ``<wake mode>``.

  - If ``<wake mode>`` is 1, ``<wake number>`` represents GPIO number for wake-up. You need to ensure that the configured GPIO wake-up pin is not used for other purposes. Otherwise, you need to perform compatibility processing.
  - If ``<wake mode>`` is 2, ``<wake number>`` represents UART number. Currently, only 1 is supported for ``<wake number>``, which means only UART1 can wake up MCU.

- **<wake signal>**: It means differently depending on the parameter ``<wake mode>``.

  - If ``<wake mode>`` is 1, ``<wake signal>`` represents wake-up level.

    - 0: Low level
    - 1: High level

  - If ``<wake mode>`` is 2, ``<wake signal>`` represents wake-up byte. Range: [0,255].

- **<delay time>**: Maximum waiting time. Unit: milliseconds. Range: [0,60000]. It means differently depending on the parameter ``<wake mode>``.

  - If ``<wake mode>`` is 1, the ``<wake signal>`` level will be held on during the ``<delay time>``. After the ``<delay time>`` is reached, the ``<wake signal>`` level is reversed.
  - If ``<wake mode>`` is 2, AT will send ``<wake signal>`` byte immediately and wait until timeout.

- **<check mcu awake method>**: AT checks whether MCU is in awake state.

  - Bit 0: Whether to enable :ref:`AT+USERMCUSLEEP <cmd-USERMCUSLEEP>` command linkage. Enabled by default. That is, when receiving AT+USERMCUSLEEP=0 command from MCU, AT knows that MCU is in awake state; when receiving AT+USERMCUSLEEP=1 command, AT knows that MCU is in sleep.
  - Bit 1: Whether to enable :ref:`AT+SLEEP=0/1/2/3 <cmd-SLEEP>` command linkage. Disabled by default. That is, when receiving AT+SLEEP=0 command, AT knows that MCU is in awake state; when receiving AT+SLEEP=1/2/3 command, AT knows that MCU is in sleep.
  - Bit 2: Whether to enable the function of indicating MCU state after ``<delay time>`` timeout. Disabled by default. That is, when disabled, it indicates that MCU is in sleep after ``<delay time>``; when enabled, it indicates that MCU is in awake state after ``<delay time>``.
  - Bit 3 (not implemented yet): Whether to enable the function of indicating MCU state via GPIO. Unsupported by default.

Notes
^^^^^

- This command needs to be configured only once.
- Each time before the AT actively sends data to MCU, it will send a wake-up signal first and then enter the waiting time. When ``<delay time>`` is reached, it will directly send data. This wait timeout will reduce the transmission efficiency with MCU.
- If AT receives any wake-up event in ``<check mcu wake method>`` before ``<delay time>``, it will immediately clear the wake-up state; otherwise, the wake-up state will be cleared automatically after the ``<delay time>`` timeout.

Example
^^^^^^^

::

    // Enable wake-up MCU configuration. Before each time the AT sends data to the MCU, it will first use the GPIO18 pin of the Wi-Fi module to wake up the MCU at a high level and hold on the high level for 10 seconds.
    AT+USERWKMCUCFG=1,1,18,1,10000,3

    // Enable wake-up configuration
    AT+USERWKMCUCFG=0

.. _cmd-USERMCUSLEEP:

:ref:`AT+USERMCUSLEEP <User-AT>`: MCU Indicates Its Sleep State
---------------------------------------------------------------

Set Command
^^^^^^^^^^^

**Function:**

This command can only take effect after the ``<check mcu wake method>`` Bit 0 of the :ref:`AT+USERWKMCUCFG <cmd-USERWKMCUCFG>` command is configured. It informs AT of the current MCU sleep state.

**Command:**

::

    AT+USERMCUSLEEP=<state>

**Response:**

::

    OK

Parameters
^^^^^^^^^^

- **<state>**:

  - 0: Indicates that MCU is in awake state.
  - 1: Indicates that MCU is in sleep state.

Example
^^^^^^^

::

    // MCU tells AT that the current MCU is in awake state
    AT+USERMCUSLEEP=0
