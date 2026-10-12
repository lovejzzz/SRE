import { normalize } from './normalize.mjs';
let input = '';
for await (const chunk of process.stdin) input += chunk;
const request = JSON.parse(input);
const steps = request.actions.map(action => {
  let value = normalize(action.normalize);
  if (process.argv.includes('--mutant') && value.startsWith('//')) value = value.slice(1);
  return { action, result: { value }, state: { stateless: true } };
});
process.stdout.write(JSON.stringify({schema_version: 1, scenario: request.scenario,
  lifecycle: { reset: true, finalize: true }, steps}));
