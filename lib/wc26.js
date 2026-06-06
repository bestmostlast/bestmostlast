import fs from "fs";
import path from "path";

const PUB = path.join(process.cwd(), "public", "wc26");

export function loadMatches() {
  return JSON.parse(fs.readFileSync(path.join(PUB, "matches.json"), "utf8")).matches;
}

export function loadTeams() {
  return JSON.parse(fs.readFileSync(path.join(PUB, "teams.json"), "utf8")).teams;
}
