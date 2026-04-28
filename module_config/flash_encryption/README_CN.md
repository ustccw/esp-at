# ESP-AT Flash 加密 + NVS 加密配置指南（开发模式）

本文档说明如何为 ESP-AT 项目启用 **Flash 加密** 和 **NVS 加密**。本文以 `module_config/module_esp32c6_default/` 为示例演示具体的修改步骤，其他模组请根据自身 flash 布局调整偏移量和大小。

> **注意**：本指南仅涵盖 **开发模式（Development Mode）**。开发模式下，Flash 加密密钥在首次启动时由芯片生成并写入 eFuse，可重新烧录的次数有限。

---

## 概述

启用 Flash 加密后，存储在 flash 中的固件和数据分区会被加密保护。NVS 加密则进一步保护 NVS 格式的分区（如 `mfg_nvs`），使用存放在 `nvs_key` 分区中的独立密钥进行加密。

**密钥文件**：`module_config/flash_encryption/sample_encryption_keys.bin`
此文件是预生成的 NVS 加密密钥，编译时用于加密 `mfg_nvs.bin`，烧录时写入 `nvs_key` 分区供运行时读取。

---

## 分步修改说明

以 `module_config/module_esp32c6_default/` 为参考示例，其他模组请根据自身 flash 布局调整偏移量和大小。

### 步骤 1：修改 `partitions_at.csv`

增加 `Flags` 列。需要 Flash 加密的分区标记 `encrypted`。新增 `nvs_key` 分区（type: `data`，subtype: `nvs_keys`）。

**修改前**（原始 `module_esp32c6_default`）：

```
# Name, Type, SubType, Offset, Size
otadata, data, ota, 0xd000, 0x2000
phy_init, data, phy, 0xf000, 0x1000
nvs, data, nvs, 0x10000, 0xE000
at_customize, 0x40, 0, 0x1E000, 0x42000
ota_0, app, ota_0, 0x60000, 0x1d0000
ota_1, app, ota_1, 0x230000, 0x1d0000
```

**修改后**：

```
# Name, Type, SubType, Offset, Size, Flags
otadata, data, ota, 0xf000, 0x2000,
phy_init, data, phy, 0x11000, 0x1000,
nvs, data, nvs, 0x12000, 0xE000,
at_customize, 0x40, 0, 0x20000, 0x3f000,
nvs_key, data, nvs_keys, 0x5f000, 0x1000, encrypted
ota_0, app, ota_0, 0x60000, 0x1d0000, encrypted
ota_1, app, ota_1, 0x230000, 0x1d0000, encrypted
```

关键改动：
- 分区表偏移从 `0x8000` 移到 `0xA000`（开启 Flash 加密后 bootloader 体积增大，所有分区需要后移）。
- 新增 `nvs_key` 分区（`data, nvs_keys`），标记 `encrypted`，用于存放 NVS 加密密钥。
- `ota_0` 和 `ota_1` 增加 `encrypted` 标记。
- `at_customize` 偏移从 `0x1E000` 调整到 `0x20000`，大小从 `0x42000` 缩减为 `0x3f000`（为 `nvs_key` 分区腾出空间，`at_customize` 结束地址 `0x5f000` 紧接 `nvs_key`）。
- `at_customize` 不加 `encrypted` 标记，编译系统以 `ALWAYS_PLAINTEXT` 方式烧录。

### 步骤 2：修改 `at_customize.csv`

调整 `mfg_nvs` 偏移以适配新的分区布局，同时缩小 `fs_storage` 以适应 `at_customize` 分区大小的变化。

**修改前**：

```
# Name, Type, SubType, Offset, Size
mfg_nvs, data, nvs, 0x1f000, 124K
fs_storage, data, 0xff, 0x47000, 100K
```

**修改后**：

```
# Name, Type, SubType, Offset, Size
mfg_nvs, data, nvs, 0x21000, 124K
fs_storage, data, 0xff, 0x47000, 70K
```

- `mfg_nvs` 偏移从 `0x1f000` 调整到 `0x21000`（= `at_customize` 偏移 `0x20000` + `0x1000` 预留空间）。
- `fs_storage` 从 100K 缩减为 70K，确保不超出 `at_customize` 分区范围（`0x47000` + 70K = `0x58800` < `0x5f000`）。

### 步骤 3：修改 `sdkconfig.defaults`

添加以下配置项。

**3.1 — 增大分区表偏移**（bootloader 体积增大）：

```
CONFIG_PARTITION_TABLE_OFFSET=0xA000
```

**3.2 — 启用 Flash 加密（开发模式）+ NVS 加密**：

```
# Flash encryption (development) + NVS encryption
CONFIG_SECURE_FLASH_ENC_ENABLED=y
CONFIG_SECURE_FLASH_ENCRYPTION_MODE_DEVELOPMENT=y
CONFIG_NVS_ENCRYPTION=y
CONFIG_SECURE_FLASH_UART_BOOTLOADER_ALLOW_ENC=y
CONFIG_SECURE_FLASH_UART_BOOTLOADER_ALLOW_DEC=y
CONFIG_SECURE_FLASH_UART_BOOTLOADER_ALLOW_CACHE=y
```

**3.3 — 更新 AT 自定义分区表偏移**（需与 `partitions_at.csv` 中 `at_customize` 的偏移一致）：

```
CONFIG_AT_CUSTOMIZED_PARTITION_TABLE_OFFSET=0x20000
```

---

## 编译

```bash
./build.py build
```

编译系统会自动：
1. 当 `CONFIG_NVS_ENCRYPTION=y` 时，使用 `sample_encryption_keys.bin` 以 **加密模式** 生成 `mfg_nvs.bin`。
2. 将 `sample_encryption_keys.bin` 加入烧录目标，对应 `nvs_key` 分区。

## 烧录

**首次烧录**（eFuse 尚未写入加密密钥）：

```bash
./build.py flash -p /dev/ttyUSBx
```

首次烧录使用普通 `flash` 命令，bootloader 会在首次启动时自动生成密钥并加密 flash。

**后续重新烧录**（eFuse 已包含加密密钥）：

```bash
esptool.py --port /dev/ttyUSBx erase_flash
./build.py encrypted-flash -p /dev/ttyUSBx -b 115200 monitor
```

`encrypted-flash` 命令会使用已有的 eFuse 密钥对标记 `encrypted` 的分区进行加密烧录。`at_customize.bin` 和 `mfg_nvs.bin` 以明文方式烧录（`ALWAYS_PLAINTEXT`），因为：
- `mfg_nvs.bin` 已在编译时被 NVS 分区生成器加密，不需要 Flash 层再次加密。
- `at_customize.bin` 为元数据表，不包含敏感数据，不需要 Flash 层加密。

## 首次启动

在空白 flash 上首次启动时：
1. Bootloader 生成 Flash 加密密钥并写入 eFuse。
2. Bootloader 对所有标记 `encrypted` 的分区进行原地加密。
3. 应用程序从 `nvs_key` 分区读取 NVS 加密密钥，用于解密 `mfg_nvs`。

日志中应看到类似输出：

```
I (xxx) flash_encrypt: Flash encryption mode is DEVELOPMENT
I (xxx) at-init: NVS encryption enabled, mfg_nvs is encrypted successfully
I (xxx) at-init: at param mode: 1
```

`at param mode: 1` 表示 `mfg_nvs` 在 NVS 加密下初始化成功。

## 开发模式限制

- Flash 加密密钥存储在 eFuse 中。开发模式下可重新烧录加密数据的次数有限（由 `SPI_BOOT_CRYPT_CNT` eFuse 控制）。
- 如需重新开始，可通过 `espefuse.py burn_efuse` 翻转 `SPI_BOOT_CRYPT_CNT` 的位，或更换芯片。
