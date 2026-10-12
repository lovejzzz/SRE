import { normalize } from './normalize.mjs';
let input = '';
for await (const chunk of process.stdin) input += chunk;
const paths = JSON.parse(input);
if (!Array.isArray(paths) || !paths.every(p => typeof p === 'string')) throw new TypeError('Expected string array');
const values = paths.map(normalize);
// Deliberate incorrect behavior to test the comparator, never used by the normal implementation.
if (process.argv.includes('--mutant')) {
  for (let i = 0; i < values.length; i++) {
    if (values[i].startsWith('//')) values[i] = values[i].slice(1);
  }
}
process.stdout.write(JSON.stringify(values));
