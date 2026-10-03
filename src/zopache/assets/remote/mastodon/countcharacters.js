const URL_LENGTH = 23; // Mastodon default
const URL_REGEX = /(?:https?:\/\/|www\.)[^\s]+/g;
const MENTION_REGEX = /(^|[^=\/\w])@([a-z0-9_]+(?:[a-z0-9_.-]+[a-z0-9_]+)?)@[a-z0-9.\-]+[a-z0-9]+/gi;

// Reused across calls; grapheme segmentation rules don't change per invocation.
const graphemeSegmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" });

function countCharacters(text) {
  const normalized = text
    .replace(URL_REGEX, "x".repeat(URL_LENGTH)) // every URL becomes 23 chars
    .replace(MENTION_REGEX, "$1@$2");           // drop the @domain part of mentions

  // Count user-perceived characters so emoji count as 1
  return [...graphemeSegmenter.segment(normalized)].length;
}
