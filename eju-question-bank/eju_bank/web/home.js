"use strict";
/* L0 入口页：读三个数字，其余都是静态链接。 */

async function loadHome() {
  await loadLibraryInstanceId();

  const status = $("#home-status");
  try {
    const { papers } = await api("/api/v1/papers");
    const usable = papers.filter((p) => !["REVIEW_REQUIRED", "SUSPENDED"].includes(p.deliveryState));
    const questions = papers.reduce((n, p) => n + (p.questionCount || 0), 0);
    $("#stat-practice").textContent =
      papers.length
        ? `可练 ${usable.length} 套卷 · 共 ${questions} 题` +
          (usable.length < papers.length ? ` · ${papers.length - usable.length} 套待复核` : "")
        : "题库中还没有已发布的试卷";
    status.textContent = "本地题库已连接";
    status.className = "home-status online";
  } catch (error) {
    $("#stat-practice").textContent = "无法读取试卷列表";
    status.textContent = "本地服务未连接";
    status.className = "home-status offline";
    throw error;
  }

  try {
    const [{ wrongQuestions }, { bookmarks }, { history }] = await Promise.all([
      api("/api/v1/wrong-questions"), api("/api/v1/bookmarks"), api("/api/v1/history?limit=1"),
    ]);
    const pending = wrongQuestions.filter((w) => w.status !== "MASTERED").length;
    const parts = [`待复习错题 ${pending}`, `收藏 ${bookmarks.length}`];
    if (history.length) parts.push(`最近练习 ${new Date(history[0].submittedAt || history[0].createdAt).toLocaleDateString()}`);
    $("#stat-me").textContent = parts.join(" · ");
  } catch {
    $("#stat-me").textContent = "学习记录暂不可读";
  }

  // 未交卷的会话直接给一条“接着做”的入口，不必先进工作区再找。
  const sid = localStorage.getItem(`eju.activeSession.${state.libraryInstanceId}`);
  if (!sid) return;
  try {
    const { session } = await api(`/api/v1/sessions/${sid}`);
    if (!["IN_PROGRESS", "PAUSED"].includes(session.status)) {
      localStorage.removeItem(`eju.activeSession.${state.libraryInstanceId}`);
      return;
    }
    const banner = $("#continue-banner");
    banner.href = `./practice#/session/${sid}`;
    $("#continue-title").textContent = `继续上次练习 · ${I18N.translateMode(session.mode)}`;
    $("#continue-detail").textContent =
      session.status === "PAUSED" ? "上次已暂停，继续后才能作答。" : "上次的作答已保留，可以直接接着做。";
    banner.hidden = false;
  } catch {
    localStorage.removeItem(`eju.activeSession.${state.libraryInstanceId}`);
  }
}

loadHome().catch(showError);
