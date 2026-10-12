// Independent JavaScript implementation of the scoped POSIX string-path contract.
// No filesystem lookup: this operation is lexical, not realpath or path resolution.
export function normalize(path) {
  if (typeof path !== 'string') throw new TypeError('Expected a string');
  const root = path.startsWith('//') && !path.startsWith('///') ? '//' : path.startsWith('/') ? '/' : '';
  const segments = [];
  for (const segment of path.split('/')) {
    if (!segment || segment === '.') continue;
    if (segment === '..') {
      if (segments.length && segments.at(-1) !== '..') segments.pop();
      else if (!root) segments.push('..');
    } else segments.push(segment);
  }
  return root + segments.join('/') || '.';
}
