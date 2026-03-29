// © 2026 arun•°Cumar
import { downloadViewOnceMedia } from '../../lib/store/emix.js';

export default async (sock, msg) => {
    const chat = msg.key.remoteJid;

    try {
        const media = await downloadViewOnceMedia(msg);

        if (!media) {
            return sock.sendMessage(chat, {
                text: "❌ Please reply to a View Once media!"
            }, { quoted: msg });
        }

        const caption = `> *Nexa-Bot MD View-Once*`;

        if (media.type === 'image') {
            await sock.sendMessage(chat, {
                image: media.buffer,
                caption
            }, { quoted: msg });
        }

        if (media.type === 'video') {
            await sock.sendMessage(chat, {
                video: media.buffer,
                caption
            }, { quoted: msg });
        }

        if (media.type === 'audio') {
            await sock.sendMessage(chat, {
                audio: media.buffer,
                mimetype: 'audio/mp4',
                ptt: false
            }, { quoted: msg });
        }

    } catch (e) {
        console.log("ViewOnce Error:", e.message);
        await sock.sendMessage(chat, {
            text: "❌ Failed to retrieve media."
        }, { quoted: msg });
    }
};
