# ADR-003: 内容寻址媒体存储与图像切片

- 状态：Accepted
- 日期：2026-09-03
- 决策人：EJU题库架构组

## 背景
EJU 试题中包含大量电路图、几何图形、实验装置示意图及听解音频。现有原型仅使用 `figure-placeholder` 占位符，无法在答题和复习时向考生真实展示图表。

## 决策
1. 采用 SHA-256 内容寻址存储（CAS）：媒体文件存放于 `library/media/{hash[:2]}/{hash}.{ext}`。
2. 在渲染和组卷阶段，根据 page contract 声明的 `sourceBbox`，使用高质量图形裁剪算法从原页渲染件提取真实切片，生成独立资产并记录尺寸、MIME 与校验哈希。
3. 交付接口：提供统一的 `GET /api/v1/media/{assetId}`，支持高效的 HTTP 206 Partial Content (Range requests) 满足音频/视频的流式播放和拖拽。
4. 阻断门禁：原卷存在必要图表而未生成切片或切片损坏时，审计必须失败，禁止作为完整卷发布。
