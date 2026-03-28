// © 2026 arun•°Cumar. All Rights Reserved.
import { checkOwner } from '../../Settings/check.js';

export default async (sock, msg, args) => {
    try {
        const from = msg.key.remoteJid;
        const sender = msg.key.participant || msg.key.remoteJid;
        const fromMe = msg.key.fromMe;

        // Owner check
        const isOwner = checkOwner(sender, fromMe);
        if (!isOwner) {
            return await sock.sendMessage(from, {
                text: "❌ Owner only command!"
            }, { quoted: msg });
        }

        // Restart message
        await sock.sendMessage(from, {
            text: "♻️ Restarting bot..."
        }, { quoted: msg });

        console.log("Bot restarting by owner...");

        // Restart
        process.exit(0);

    } catch (err) {
        console.log("Restart Error:", err);
        await sock.sendMessage(msg.key.remoteJid, {
            text: "❌ Restart failed."
        }, { quoted: msg });
    }
};
