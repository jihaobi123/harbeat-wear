# Flow Ring V0.1

Flow Ring 使用 Seeed Studio XIAO nRF54L15 Sense 验证舞蹈手势音效触发。

## 当前阶段

- 主控：nRF54L15；
- IMU：板载 LSM6DS3TR-C；
- 固件：nRF Connect SDK 3.4.0 / Zephyr；
- 构建目标：`xiao_nrf54l15/nrf54l15/cpuapp`；
- 触摸：当前用 USER 按键模拟，预留外置电容触摸；
- 反馈：当前用 LED 模拟，预留 DRV2605L 和 LRA；
- 主开发系统：Windows 11 x64。

完整功能、协议、引脚、测试和开发流程见 [V0.1 设计文档](docs/2026-08-28-flow-ring-xiao-nrf54l15-v0.1-design.md)。

当前目录先保存已经批准的设计，固件代码按实施计划逐步加入。
