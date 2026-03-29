// © 2026 arun•°Cumar. All Rights Reserved.
export default async function tagAll(sock, msg, args) {
    const chatId = msg.key.remoteJid;

    if (!chatId.endsWith('@g.us')) {
        return await sock.sendMessage(chatId, {
            text: '❌ This command can only be used in groups.'
        });
    }

    try {
        const metadata = await sock.groupMetadata(chatId);
        const participants = metadata.participants;

        if (!participants.length) {
            return sock.sendMessage(chatId, { text: 'No members found.' });
        }

        const chunkSize = 20; 
        const chunks = [];

        for (let i = 0; i < participants.length; i += chunkSize) {
            chunks.push(participants.slice(i, i + chunkSize));
        }

        for (let chunk of chunks) {
            let text = `📢 *TAG ALL*\n\n`;

            for (let user of chunk) {
                text += `🔹 @${user.id.split('@')[0]}\n`;
            }

            await sock.sendMessage(chatId, {
                text,
                mentions: chunk.map(u => u.id)
            }, { quoted: msg });

            // delay to avoid spam/ban
            await new Promise(res => setTimeout(res, 1000));
        }

    } catch (err) {
        console.error("TagAll Error:", err);
        await sock.sendMessage(chatId, {
            text: '❌ Failed. Make sure I am admin.'
        });
      }
    }
