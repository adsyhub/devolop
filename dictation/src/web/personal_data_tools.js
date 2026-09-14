"use strict";

/* Pure parsing and identity helpers for the personal centre. */

const PersonalDataTools = (() => {
  function vocabNaturalKey(entry) {
    const sourceRef = String(entry?.sourceRef || "").trim();
    if (sourceRef) {
      return `source:${sourceRef}\u0000${String(entry?.promptType || "recall")}\u0000${String(entry?.variantKey || "default")}`;
    }
    const term = String(entry?.term || "").trim().toLocaleLowerCase();
    const reading = String(entry?.reading || "").trim().toLocaleLowerCase();
    return term ? `${term}\u0000${reading}` : "";
  }

  function dedupeVocabEntries(items) {
    const byNaturalKey = new Map();
    (items || []).forEach((item) => {
      const key = vocabNaturalKey(item);
      if (!key) return;
      const previous = byNaturalKey.get(key);
      if (!previous || String(item.updatedAt || "") >= String(previous.updatedAt || "")) {
        byNaturalKey.set(key, item);
      }
    });
    return [...byNaturalKey.values()];
  }

  function parseVocabImport(raw) {
    const items = [];
    let errors = 0;
    String(raw || "").split(/\r?\n/).forEach((sourceLine) => {
      const line = sourceLine.trim();
      if (!line || line.startsWith("#")) return;
      const delimiter = line.includes("\t") ? "\t" : ",";
      const fields = parseDelimitedFields(line, delimiter);
      const term = String(fields[0] || "").trim();
      if (!term) {
        errors += 1;
        return;
      }
      const rawTags = String(fields[4] || "").trim();
      const tags = rawTags ? rawTags.split(/[\s,，]+/).map((tag) => tag.trim()).filter(Boolean) : [];
      const level = tags.find((tag) => /^N[1-5]$/i.test(tag))?.toUpperCase() || "";
      items.push({
        term,
        reading: String(fields[1] || "").trim(),
        meaning: String(fields[2] || "").trim(),
        note: String(fields[3] || "").trim(),
        tags,
        level,
      });
    });
    return { items, errors };
  }

  function parseDelimitedFields(line, delimiter) {
    const fields = [];
    let value = "";
    let quoted = false;
    for (let index = 0; index < line.length; index += 1) {
      const char = line[index];
      if (char === '"') {
        if (quoted && line[index + 1] === '"') {
          value += '"';
          index += 1;
        } else {
          quoted = !quoted;
        }
      } else if (char === delimiter && !quoted) {
        fields.push(value);
        value = "";
      } else {
        value += char;
      }
    }
    fields.push(value);
    return fields;
  }

  return { dedupeVocabEntries, parseDelimitedFields, parseVocabImport, vocabNaturalKey };
})();
