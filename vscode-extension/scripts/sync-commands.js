const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const pkgPath = path.join(root, 'package.json');
const commandsPath = path.join(root, 'commands.json');

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function writeJson(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n', 'utf8');
}

function main() {
  if (!fs.existsSync(commandsPath)) {
    console.error('commands.json not found at', commandsPath);
    process.exit(1);
  }

  const commands = readJson(commandsPath);
  const pkg = readJson(pkgPath);

  if (!pkg.contributes) pkg.contributes = {};
  pkg.contributes.commands = pkg.contributes.commands || [];

  const existingIds = new Set(pkg.contributes.commands.map(c => c.command));
  for (const c of commands) {
    if (!existingIds.has(c.command)) {
      pkg.contributes.commands.push({ command: c.command, title: c.title });
      existingIds.add(c.command);
    }
  }

  writeJson(pkgPath, pkg);
  console.log('Synced', commands.length, 'commands into', pkgPath);
}

main();
