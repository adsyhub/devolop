# JLPT 题库系统 74 条核心验收项追踪矩阵

> 基线需求：《JLPT N1/N2 真题题库系统——最终可执行规格》（`docs/题库` 第 33 节）  
> 审计基线：`docs/JLPT_题库差距分析与执行计划.md`  
> 状态定义：  
> - `PASSED`：代码已实现并通过自动化测试验证；  
> - `EXEMPT`：合规豁免（需求允许首版不启用，如非官方估分模型）；  
> - `IN_PROGRESS`：本期正在补全实现；  

---

## 1. 等级和题型（8 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| K01 | 公开接口只接受 N1/N2 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k01_public_api_only_accepts_n1_n2` | `src/exam_models.py`, `src/exam_api_v1.py` |
| K02 | 后台只允许 N1/N2 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k02_admin_only_allows_n1_n2` | `src/exam_models.py`, `src/exam_api_v1.py` |
| K03 | N1 不出现表记 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k03_n1_refuses_orthography` | `src/exam_models.py`, `src/exam_db.py` |
| K04 | N1 不出现构词 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k04_n1_refuses_word_formation` | `src/exam_models.py`, `src/exam_db.py` |
| K05 | N2 不出现独立长篇阅读 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k05_n2_refuses_reading_long` | `src/exam_models.py`, `src/exam_db.py` |
| K06 | N1/N2 听力题型矩阵正确 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k06_listening_matrix_valid` | `src/exam_models.py` |
| K07 | 非法组合在服务端被拒绝 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k07_invalid_combination_rejected_by_server` | `src/exam_models.py`, `src/exam_engine.py` |
| K08 | 非法组合在数据库层被拒绝 | PASSED | `test_exam_v2_matrix.MatrixTests.test_k08_invalid_combination_rejected_by_db` | `src/exam_db.py` |

---

## 2. 套卷和版本（6 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| V01 | 同一题组可被多个入口复用 | PASSED | `test_exam_v2_session.SessionTests.test_v01_group_reusable_across_modes` | `src/exam_engine.py` |
| V02 | 发布套卷引用明确题组版本 | PASSED | `test_exam_v2_session.SessionTests.test_v02_paper_references_group_versions` | `src/exam_models.py`, `src/exam_db.py` |
| V03 | 新题组版本不改变旧场次 | PASSED | `test_exam_v2_session.SessionTests.test_v03_new_version_does_not_affect_old_session` | `src/exam_engine.py` |
| V04 | 套卷顺序可完整复现 | PASSED | `test_exam_v2_session.SessionTests.test_v04_paper_order_reproducible` | `src/exam_engine.py` |
| V05 | 官方选编不误标为完整原卷 | PASSED | `test_exam_v2_session.SessionTests.test_v05_authenticity_and_completeness_labels` | `src/exam_models.py` |
| V06 | 发布版本不可直接修改 | PASSED | `test_exam_v2_session.SessionTests.test_v06_published_version_immutable` | `src/exam_db.py` |

---

## 3. 版权（6 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| R01 | 权利未批准无法发布 | PASSED | `test_exam_v2_rights.RightsTests.test_r01_unapproved_cannot_publish` | `src/exam_rights.py` |
| R02 | 许可过期无法创建新场次 | PASSED | `test_exam_v2_rights.RightsTests.test_r02_expired_license_cannot_start_session` | `src/exam_rights.py`, `src/exam_engine.py` |
| R03 | 翻译权限关闭时不返回翻译 | PASSED | `test_exam_v2_rights.RightsTests.test_r03_translation_disabled_strips_translation` | `src/exam_rights.py` |
| R04 | 音频权限关闭时不返回音频凭证 | PASSED | `test_exam_v2_rights.RightsTests.test_r04_audio_disabled_strips_credentials` | `src/exam_rights.py` |
| R05 | 下架有审计日志 | PASSED | `test_exam_v2_rights.RightsTests.test_r05_suspend_has_audit_log` | `src/exam_rights.py`, `src/exam_db.py` |
| R06 | 权利撤销后不能生成媒体签名 | PASSED | `test_exam_v2_rights.RightsTests.test_r06_revoked_rights_refuse_media_signature` | `src/exam_rights.py` |

---

## 4. 普通练习（8 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| P01 | 选择答案后自动保存 | PASSED | `test_exam_v2_session.SessionTests.test_p01_autosave_answers` | `src/exam_engine.py` |
| P02 | 刷新后答案恢复 | PASSED | `test_exam_v2_session.SessionTests.test_p02_session_answers_restored` | `src/exam_engine.py`, `src/exam_api_v1.py` |
| P03 | 刷新后当前位置恢复 | PASSED | `test_exam_v2_session.SessionTests.test_p03_session_position_restored` | `src/exam_engine.py`, `src/exam_api_v1.py` |
| P04 | 逐题和整组提交正确 | PASSED | `test_exam_v2_session.SessionTests.test_p04_group_and_item_submit` | `src/exam_engine.py` |
| P05 | 提交前接口不含答案 | PASSED | `test_exam_v2_session.SessionTests.test_p05_delivery_dto_contains_no_answer` | `src/exam_engine.py` |
| P06 | 阅读上下文完整 | PASSED | `test_exam_v2_session.SessionTests.test_p06_reading_context_intact` | `src/exam_engine.py` |
| P07 | 听力上下文完整 | PASSED | `test_exam_v2_session.SessionTests.test_p07_listening_context_intact` | `src/exam_engine.py` |
| P08 | 新场次不覆盖旧场次 | PASSED | `test_exam_v2_session.SessionTests.test_p08_new_session_does_not_overwrite_old` | `src/exam_engine.py` |

---

## 5. 严格模考（16 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| E01 | N1 第一科 110 分钟来自配置 | PASSED | `test_exam_v2_mock.MockTests.test_e01_n1_section1_duration_from_blueprint` | `src/exam_models.py` |
| E02 | N1 听力 55 分钟来自配置 | PASSED | `test_exam_v2_mock.MockTests.test_e02_n1_section2_duration_from_blueprint` | `src/exam_models.py` |
| E03 | N2 第一科 105 分钟来自配置 | PASSED | `test_exam_v2_mock.MockTests.test_e03_n2_section1_duration_from_blueprint` | `src/exam_models.py` |
| E04 | N2 听力 50 分钟来自配置 | PASSED | `test_exam_v2_mock.MockTests.test_e04_n2_section2_duration_from_blueprint` | `src/exam_models.py` |
| E05 | 修改浏览器时间不影响倒计时 | PASSED | `test_exam_v2_mock.MockTests.test_e05_client_time_does_not_alter_server_countdown` | `src/exam_engine.py` |
| E06 | 页面刷新不重置时间 | PASSED | `test_exam_v2_mock.MockTests.test_e06_refresh_does_not_reset_deadline` | `src/exam_engine.py` |
| E07 | 换设备不重置时间 | PASSED | `test_exam_v2_mock.MockTests.test_e07_switch_device_does_not_reset_deadline` | `src/exam_engine.py` |
| E08 | 第一科提交后不能返回 | PASSED | `test_exam_v2_mock.MockTests.test_e08_submitted_section_cannot_modify_answers` | `src/exam_engine.py` |
| E09 | 到时自动提交 | PASSED | `test_exam_v2_mock.MockTests.test_e09_auto_submit_on_expiry` | `src/exam_engine.py` |
| E10 | 截止后答案被拒绝 | PASSED | `test_exam_v2_mock.MockTests.test_e10_answers_rejected_after_deadline` | `src/exam_engine.py` |
| E11 | 听力不能拖动 | PASSED | `test_exam_v2_mock.MockTests.test_e11_audio_player_policy_no_seek` | `src/exam_models.py` |
| E12 | 听力不能倍速 | PASSED | `test_exam_v2_mock.MockTests.test_e12_audio_player_policy_no_rate_change` | `src/exam_models.py` |
| E13 | 听力不能主动暂停 | PASSED | `test_exam_v2_mock.MockTests.test_e13_audio_player_policy_no_pause` | `src/exam_models.py` |
| E14 | 听力不能主动重播 | PASSED | `test_exam_v2_mock.MockTests.test_e14_audio_player_policy_no_replay` | `src/exam_models.py` |
| E15 | 重复提交幂等 | PASSED | `test_exam_v2_mock.MockTests.test_e15_duplicate_submit_idempotent` | `src/exam_engine.py` |
| E16 | 多标签页不能延长时间 | PASSED | `test_exam_v2_mock.MockTests.test_e16_lease_prevents_extension_across_tabs` | `src/exam_engine.py` |

---

## 6. 动态练习（9 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| D01 | 抽题单位是题组 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d01_draw_unit_is_question_group` | `src/exam_engine.py` |
| D02 | 单场无重复题组 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d02_no_duplicate_groups_in_session` | `src/exam_engine.py` |
| D03 | `UNSEEN` 筛选正确 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d03_unseen_filter` | `src/exam_engine.py` |
| D04 | `WRONG` 筛选正确 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d04_wrong_filter` | `src/exam_engine.py` |
| D05 | `DUE` 筛选正确 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d05_due_filter` | `src/exam_engine.py` |
| D06 | 排除最近练习正确 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d06_exclude_recent_days` | `src/exam_engine.py` |
| D07 | 题量不足返回 warning | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d07_insufficient_questions_returns_warning` | `src/exam_engine.py` |
| D08 | 快照不受后续标签修改影响 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d08_session_snapshot_immune_to_tag_update` | `src/exam_engine.py` |
| D09 | 不自动生成新题补齐 | PASSED | `test_exam_v2_dynamic.DynamicTests.test_d09_no_synthetic_fabrication_to_fill_pool` | `src/exam_engine.py` |

---

## 7. 报告和复习（12 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| A01 | 分别统计语言知识、阅读、听力 | PASSED | `test_exam_v2_report.ReportTests.test_a01_sections_scored_separately` | `src/exam_engine.py` |
| A02 | 保存首次结果 | PASSED | `test_exam_v2_report.ReportTests.test_a02_first_result_preserved` | `src/exam_engine.py` |
| A03 | 保存最近结果 | PASSED | `test_exam_v2_report.ReportTests.test_a03_latest_result_preserved` | `src/exam_engine.py` |
| A04 | 保存最好结果 | PASSED | `test_exam_v2_report.ReportTests.test_a04_best_result_preserved` | `src/exam_engine.py` |
| A05 | 保存全部历史 | PASSED | `test_exam_v2_report.ReportTests.test_a05_all_attempts_preserved` | `src/exam_engine.py` |
| A06 | 无估分模型时不显示精确估分 | PASSED | `test_exam_v2_report.ReportTests.test_a06_no_fake_official_score` | `src/exam_engine.py` |
| A07 | 有估分时显示模型版本 | EXEMPT | 合规豁免：首版未启用估分模型 | `src/exam_engine.py` |
| A08 | 有估分时显示“非官方估算” | EXEMPT | 合规豁免：首版未启用估分模型 | `src/exam_engine.py` |
| A09 | 错题重做不覆盖原场次 | PASSED | `test_exam_v2_report.ReportTests.test_a09_wrong_redo_does_not_overwrite` | `src/exam_engine.py` |
| A10 | 阅读错题重做显示完整文章 | PASSED | `test_exam_v2_report.ReportTests.test_a10_reading_redo_preserves_passage` | `src/exam_engine.py` |
| A11 | 听力错题重做显示完整音频题组 | PASSED | `test_exam_v2_report.ReportTests.test_a11_listening_redo_preserves_audio_group` | `src/exam_engine.py` |
| A12 | 掌握状态按间隔规则更新 | PASSED | `test_exam_v2_report.ReportTests.test_a12_srs_state_machine_intervals` | `src/exam_engine.py` |

---

## 8. 安全（9 项）

| ID | 验收项 | 状态 | 验证测试 | 实现模块 |
|---|---|:---:|---|---|
| S01 | 普通用户不能访问管理接口 | PASSED | `test_exam_v2_security.SecurityTests.test_s01_learner_cannot_access_admin_api` | `src/exam_rights.py`, `src/exam_api_v1.py` |
| S02 | 用户不能访问他人场次 | PASSED | `test_exam_v2_security.SecurityTests.test_s02_cannot_access_other_users_session` | `src/exam_engine.py`, `src/exam_api_v1.py` |
| S03 | 媒体 URL 短期有效 | PASSED | `test_exam_v2_security.SecurityTests.test_s03_media_tokens_short_lived` | `src/exam_rights.py` |
| S04 | 日志不含完整题目 | PASSED | `test_exam_v2_security.SecurityTests.test_s04_logs_sanitize_question_text` | `src/exam_engine.py` |
| S05 | 日志不含正确答案 | PASSED | `test_exam_v2_security.SecurityTests.test_s05_logs_sanitize_correct_answers` | `src/exam_engine.py` |
| S06 | 发布和下架有审计 | PASSED | `test_exam_v2_rights.RightsTests.test_r05_suspend_has_audit_log` | `src/exam_rights.py` |
| S07 | 富文本经过白名单清洗 | PASSED | `tests/exam_markup.test.mjs` (Node) + `test_exam_schema.AuditTests` | `src/web/exam_markup.js`, `src/exam_schema.py` |
| S08 | 答案不是通过前端隐藏 | PASSED | `test_exam_v2_security.SecurityTests.test_s08_answers_not_in_delivery_payload` | `src/exam_engine.py` |
| S09 | 严格模考截止时间由服务端判断 | PASSED | `test_exam_v2_security.SecurityTests.test_s09_deadline_enforced_by_server` | `src/exam_engine.py` |

