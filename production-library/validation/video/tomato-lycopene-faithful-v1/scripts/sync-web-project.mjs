import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const project=JSON.parse(await fs.readFile(path.join(root,'project.json'),'utf8'));
await fs.writeFile(path.join(root,'web/project-data.js'),`window.__PROJECT__=window.__PROJECT__||${JSON.stringify(project)};\n`);
console.log(path.join(root,'web/project-data.js'));
