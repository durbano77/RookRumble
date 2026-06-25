export const appearanceStorageKey = "rook-rumble-appearance";

export const appearanceOptions = {
  theme: ["forest", "midnight", "paper", "ocean", "berry"],
  pattern: ["argyle", "dots", "grid", "plain"],
  board: ["classic", "slate", "sand", "contrast"],
  pieces: ["classic", "three_d", "woodcut", "marble"],
};

export const pieceSymbols = {
  P: "♟", N: "♞", B: "♝", R: "♜", Q: "♛", K: "♚",
  p: "♟", n: "♞", b: "♝", r: "♜", q: "♛", k: "♚",
};

export const defaultVariants = [
  { id: "classic",     label: "Classic",          description: "Regular chess, clean and familiar." },
  { id: "three_check", label: "Three-Check",       description: "Win by checking the enemy king three times." },
  { id: "king_hill",   label: "King of the Hill",  description: "Win by marching your king into the center." },
  { id: "atomic",      label: "Atomic",            description: "Captures explode nearby pieces." },
  { id: "dice",        label: "Dice Chess",        description: "A die chooses which piece type must move." },
  { id: "fog",         label: "Fog of War",        description: "You only see what your army can reach." },
  { id: "thress",      label: "Thress",            description: "Every third move, pick one of three silly rule cards." },
];

export const variantCardMeta = {
  classic:     { icon: "♔", gradient: "linear-gradient(160deg, #ffeaa7 0%, #fdcb6e 55%, #e17055 100%)" },
  three_check: { icon: "♚", gradient: "linear-gradient(160deg, #fab1a0 0%, #ff7675 55%, #d63031 100%)" },
  king_hill:   { icon: "⛰", gradient: "linear-gradient(160deg, #55efc4 0%, #00b894 55%, #0984e3 100%)" },
  atomic:      { icon: "💥", gradient: "linear-gradient(160deg, #ffeaa7 0%, #fd79a8 50%, #e84393 100%)" },
  dice:        { icon: "🎲", gradient: "linear-gradient(160deg, #a29bfe 0%, #6c5ce7 55%, #341f97 100%)" },
  fog:         { icon: "🌫", gradient: "linear-gradient(160deg, #dfe6e9 0%, #b2bec3 55%, #636e72 100%)" },
  thress:      { icon: "🃏", gradient: "linear-gradient(160deg, #fd79a8 0%, #fdcb6e 50%, #00cec9 100%)" },
};

export const defaultVariantCardMeta = {
  icon: "♟",
  gradient: "linear-gradient(160deg, #dfe6e9 0%, #b2bec3 55%, #636e72 100%)",
};

export const defaultBotDifficulties = [
  { id: "easy",          label: "Easy Explorer",        description: "Mostly random legal moves while it learns what the pieces do." },
  { id: "medium",        label: "Balanced Club Bot",    description: "A normal casual opponent that likes sensible tactics." },
  { id: "hard",          label: "Hard Grinder",         description: "Low-chaos material play with sharper tactical priorities." },
  { id: "dougdoug",      label: "DougDoug Chaos",       description: "Unofficially inspired by streamer-brain chess: fearless, confused, funny." },
  { id: "greedy_goblin", label: "Greedy Goblin",        description: "If it can capture something, it probably will." },
  { id: "coffeehouse",   label: "Coffeehouse Attacker", description: "Checks, threats, sacrifices, vibes. Hates quiet positions." },
  { id: "gotham",        label: "Gotham Tactics",       description: "Unofficial GothamChess-flavored bot: tactical, instructive, and solid." },
  { id: "magnus",        label: "Magnus-ish Endboss",   description: "Unofficial elite-flavored bot: calm, flexible, and hard to trick." },
];
