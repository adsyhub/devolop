"use strict";

/* Pure hinting and grading rules for dictation attempts. */
const DictationScoring = (() => {
  function buildHint(answer, level, useWords) {
    if (useWords) {
      const parts = answer.split(/(\s+)/u);
      const wordIndexes = parts
        .map((part, index) => (/\p{L}|\p{N}/u.test(part) ? index : -1))
        .filter((index) => index >= 0);
      if (wordIndexes.length <= 1) {
        const characters = [...answer];
        const meaningfulCount = characters.filter((character) => /[\p{L}\p{N}]/u.test(character)).length;
        const visible = Math.max(1, Math.ceil(meaningfulCount * (level / 4)));
        let revealed = 0;
        let openingEnd = 0;
        const masked = characters.map((character, index) => {
          if (!/[\p{L}\p{N}]/u.test(character)) return character;
          revealed += 1;
          if (revealed <= visible) openingEnd = index + 1;
          return revealed <= visible ? character : "□";
        }).join("");
        return { masked, unitCount: wordIndexes.length || 1, opening: characters.slice(0, openingEnd).join("") };
      }
      const visible = Math.max(1, Math.ceil(wordIndexes.length * (level / 4)));
      const visibleSet = new Set(wordIndexes.slice(0, visible));
      const masked = parts.map((part, index) => {
        if (/^\s+$/u.test(part) || visibleSet.has(index)) return part;
        return [...part].map((character) => /[\p{P}\p{S}]/u.test(character) ? character : "□").join("");
      }).join("");
      return { masked, unitCount: wordIndexes.length, opening: parts.slice(0, (wordIndexes[visible - 1] ?? 0) + 1).join("") };
    }
    const characters = [...answer];
    const meaningful = characters.map((character, index) => /\s|[\p{P}\p{S}]/u.test(character) ? -1 : index)
      .filter((index) => index >= 0);
    const visible = Math.max(1, Math.ceil(meaningful.length * (level / 4)));
    const visibleSet = new Set(meaningful.slice(0, visible));
    const masked = characters.map((character, index) => {
      if (/\s|[\p{P}\p{S}]/u.test(character)) return character;
      return visibleSet.has(index) ? character : "□";
    }).join("");
    const openingEnd = meaningful[Math.max(0, visible - 1)] ?? 0;
    return { masked, unitCount: meaningful.length, opening: characters.slice(0, openingEnd + 1).join("") };
  }

  function normalizeAnswer(value, mode, profile) {
    const normalized = String(value || "").normalize("NFKC").trim();
    if (mode === "strict") return normalized;
    let result = profile?.latin
      ? normalized.toLocaleLowerCase(profile.locale || undefined)
      : normalized;
    if (mode === "accent-flexible" && profile?.latin) {
      result = result.normalize("NFD").replace(/\p{M}+/gu, "");
    }
    return result.replace(/[\s\p{P}\p{S}]+/gu, "");
  }

  function compareCharacters(expected, actual) {
    const left = [...expected];
    const right = [...actual];
    const matrix = Array.from({ length: left.length + 1 }, () => Array(right.length + 1).fill(0));
    for (let row = 0; row <= left.length; row += 1) matrix[row][0] = row;
    for (let col = 0; col <= right.length; col += 1) matrix[0][col] = col;
    for (let row = 1; row <= left.length; row += 1) {
      for (let col = 1; col <= right.length; col += 1) {
        const cost = left[row - 1] === right[col - 1] ? 0 : 1;
        matrix[row][col] = Math.min(
          matrix[row - 1][col] + 1,
          matrix[row][col - 1] + 1,
          matrix[row - 1][col - 1] + cost,
        );
      }
    }
    const operations = [];
    let row = left.length;
    let col = right.length;
    while (row > 0 || col > 0) {
      if (row > 0 && col > 0 && left[row - 1] === right[col - 1]) {
        operations.push({ type: "match", expected: left[row - 1], actual: right[col - 1] });
        row -= 1; col -= 1;
      } else if (row > 0 && col > 0 && matrix[row][col] === matrix[row - 1][col - 1] + 1) {
        operations.push({ type: "replace", expected: left[row - 1], actual: right[col - 1] });
        row -= 1; col -= 1;
      } else if (row > 0 && matrix[row][col] === matrix[row - 1][col] + 1) {
        operations.push({ type: "delete", expected: left[row - 1], actual: "" });
        row -= 1;
      } else {
        operations.push({ type: "insert", expected: "", actual: right[col - 1] });
        col -= 1;
      }
    }
    return { operations: operations.reverse(), distance: matrix[left.length][right.length] };
  }

  function similarityPercent(expected, actual, distance) {
    const size = Math.max([...expected].length, [...actual].length, 1);
    return Math.max(0, Math.round((1 - distance / size) * 100));
  }

  return { buildHint, normalizeAnswer, compareCharacters, similarityPercent };
})();

if (typeof module !== "undefined" && module.exports) module.exports = DictationScoring;
if (typeof window !== "undefined") window.DictationScoring = DictationScoring;
