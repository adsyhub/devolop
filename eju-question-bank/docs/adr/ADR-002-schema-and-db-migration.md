# ADR-002: 数据库迁移与版本化控制

- 状态：Accepted
- 日期：2026-09-03
- 决策人：EJU题库架构组

## 背景
从 0.1.0 原型升级到 1.0 生产级题库，需要新增资产表、审计决策、答题事件流水、错题本、书签和笔记。已有的 SQLite 数据库（如 `eju-smoke.db` 或已有练习记录）不能因 schema 升级而被破坏。

## 决策
1. 引入统一迁移控制表 `schema_migrations`，记录每次应用的 `version`、`name` 和 `applied_at`。
2. 迁移按次序增量执行，支持对空库直接跑全量迁移，或从已有的 v1 原型表升级。
3. 关键业务实体（`paper_versions`, `question_versions`）在发布状态下保持不可变，由 SQLite 触发器（Trigger）进行强约束。
4. 提供 `eju-bank db migrate` 和 `eju-bank db check` 运维命令，保证在任何启动和升级时能自动检测并报告一致性状态。
