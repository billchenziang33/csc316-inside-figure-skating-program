# FS-Jump3D · CSC316 Blender 动作库

本目录收录 FS-Jump3D 的 253 段录制：Axel、Salchow、Toe loop、Loop、Flip、Lutz 各 40 段，连跳 13 段。动作以匿名采集者 A–D 和源文件编号命名。源目录未标记每一跳的周数，因此不据文件名给片段加上 1A、2A 或 3A 等标签。网站的 50 类比赛动作覆盖表与本数据集分开维护。

原始数据：[FS-Jump3D（Ryota Takeda 等）](https://github.com/ryota-skating/FS-Jump3D)，[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。下载的是包含 2026 年 5 月 Skater_A Salchow/Toeloop 文件名修正的官方 C3D 包。`00-source/c3d-corrected-2026-05.zip` 的 SHA-256 为 `e700d90a81061181c18d9b0019be8c799959e46e42b969263b64f1ea394f7e8e`。网页导出的改编动作采用同一许可。出处与许可全文随包保存。

人物、冰场和空看台沿用 CSC316 V178 场景；默认 Blender Scene 的 Camera、Cube、Light 保留。冰鞋使用经修改的 [Ice Skates，IsaacTheMaverick](https://sketchfab.com/3d-models/623771273fd44848bd3e4e55dc358190)，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。播放器使用 [Three.js r160 与 GLTFLoader](https://github.com/mrdoob/three.js)，MIT；[许可全文](../LICENSE.THREE.txt)。

1. **r1：初次重定向。** 读取 60 fps 的 34 个 C3D 标记。将毫米转换为米，先拟合各采集时段的冰面，裁掉两端无效数据并按骨盆相对位置补内部缺失，然后应用到 V178 人物。保留原始动作和缺失范围作为对照。
2. **r2：连续性和接触。** 对骨盆相对的标记异常做局部中值筛查，温和时间平滑。以稳定段长重建手臂，以两段反向运动学重建膝关节；使用鞋尖、鞋跟和前掌平面估计鞋靴姿态，约束可见钢刀不穿冰。
3. **r3：几何和展示。** 以冰鞋和对侧大腿、小腿及冰刀的几何检测引导分离，平滑分离量。保留冰鞋近景；侧视和正视相对于冰场保持固定朝向，画面跟随人物位置。使用实际导出的骨盆轨迹测量高度、水平位移与起跳至落冰距离。

每段以 `类别/片段 ID/` 保存 `source-markers.npz`、`record.json`、各轮 `.blend`、对应 `-web.glb` 和 `rN-metrics.json`。指标包含构建脚本和输入哈希。`r3-mesh-audit.json` 记录实际受测 `.blend` 哈希、可见网格相交、膝盖弯曲方向和冰刀最小间隙。文件存在表示生成完成；只有匹配的审计才能证明其几何采样状态。第一段 `Skater_A-Axel-01` 的事件估计为 f132 起跳、f145 最高、f163 落冰，300 帧、60 fps；r3 在 2,393 个姿态样本无反向膝盖，1,197 个网格样本无对侧相交，最小刀片间隙约 1.94 mm。

动作、阶段和测量均为 **illustrative / simulated**：原始采集经过通用人物重定向、补帧和几何修正，没有使用北京冬奥运动员的比赛捕捉数据。阶段由采样估计，刀片低点并不证明真实刃别；离散网格检查并不证明所有任意插值时刻绝无穿模，也不能代替侧视、正视、近景和慢速的人工复核。r1、r2 用于比较，可能显示尚未修复的问题。
