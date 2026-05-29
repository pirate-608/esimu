import * as readline from "node:readline";

export function ask(question: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

export async function askNumber(
  question: string,
  fallback: number
): Promise<number> {
  const answer = await ask(question);
  if (!answer) return fallback;
  const n = parseInt(answer, 10);
  return isNaN(n) ? fallback : n;
}

export async function askYesNo(question: string): Promise<boolean> {
  const answer = await ask(question + " (y/n): ");
  return answer.toLowerCase().startsWith("y");
}
