import { runtime, aliveDesigns } from '../../lib/functions.js';
import fs from 'fs';

export default async (sock, msg) => {
    try {
        const from = msg.key.remoteJid;

        const uptime = runtime(process.uptime());
        const user = msg.pushName || "User";
        const date = new Date().toLocaleDateString();
        const time = new Date().toLocaleTimeString();

        // Random Design
        const design = aliveDesigns[Math.floor(Math.random() * aliveDesigns.length)];

        const aliveText = design
            .replace('{user}', user)
            .replace('{uptime}', uptime)
            .replace('{date}', date)
            .replace('{time}', time);

        await sock.sendMessage(from, {
            image: fs.readFileSync('./media/nexa.jpg'),
            caption: aliveText
        }, { quoted: msg });

    } catch (err) {
        console.log("Uptime Error:", err);
    }
};
