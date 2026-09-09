import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, join, dirname } from 'node:path';
import { createInterface } from 'node:readline';
import { homedir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';

const runtime = process.env.ZCODE_DESKTOP_HOME
  || join(process.env.XDG_DATA_HOME || join(homedir(), '.local/share'), 'computer-use-linux');
const sdk = join(runtime, 'node_modules/@modelcontextprotocol/sdk/dist/esm/client');
let Client, StdioClientTransport;
try {
  ({ Client } = await import(pathToFileURL(join(sdk, 'index.js')).href));
  ({ StdioClientTransport } = await import(pathToFileURL(join(sdk, 'stdio.js')).href));
} catch (error) {
  throw new Error('MCP SDK is missing. Run this skill\'s scripts/setup-desktop.sh first.', { cause: error });
}

if (!process.argv[2]) throw new Error('Usage: desktop-console.mjs /absolute/evidence-directory');
const evidence = resolve(process.argv[2]);
await mkdir(evidence, { recursive: true });
const client = new Client({ name: 'linux-desktop-console', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: 'bash',
  args: [join(dirname(fileURLToPath(import.meta.url)), 'start-desktop.sh')],
  env: { ...process.env },
  stderr: 'inherit',
});
await client.connect(transport);
const tools = await client.listTools();
await writeFile(join(evidence, 'tools.json'), JSON.stringify(tools, null, 2));
console.log(JSON.stringify({ connected: true, tools: tools.tools.map(tool => tool.name), evidence }));
const input = createInterface({ input: process.stdin, terminal: false });
try {
  for await (const line of input) {
    if (!line.trim()) continue;
    const request = JSON.parse(line);
    if (request.close) break;
    const label = request.label ?? `${Date.now()}-${request.tool}`;
    const file = join(evidence, `${label}.json`);
    try {
      const result = await client.callTool({ name: request.tool, arguments: request.args ?? {} }, undefined, { timeout: 60000 });
      const content = [];
      for (const [index, block] of (result.content ?? []).entries()) {
        if (block.type === 'image') {
          const path = join(evidence, `${label}-${index}.${block.mimeType === 'image/jpeg' ? 'jpg' : 'png'}`);
          await writeFile(path, Buffer.from(block.data, 'base64'));
          content.push({ type: 'image', path, mimeType: block.mimeType });
        } else content.push(block);
      }
      await writeFile(file, JSON.stringify({ request, observed_at: new Date().toISOString(), ...result, content }, null, 2));
      console.log(JSON.stringify({ label, file, isError: result.isError, result: result.structuredContent?.message, nodes: result.structuredContent?.accessibility_tree?.length, images: content.filter(block => block.type === 'image') }));
    } catch (error) {
      const failure = { request, observed_at: new Date().toISOString(), error: String(error), outcome: 'Inspect current UI before retrying a mutating request.' };
      await writeFile(file, JSON.stringify(failure, null, 2));
      console.log(JSON.stringify({ ...failure, file }));
    }
  }
} finally {
  await client.close();
  input.close();
}
