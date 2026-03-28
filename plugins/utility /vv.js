import { downloadContentFromMessage } from '@whiskeysockets/baileys'; 
import { toViewOncePhoto, toViewOnceVideo, toViewOnceVoice } from '../../lib/store/emix.js';

export default async (sock, msg, { from, quoted, body }) => {
    try {
        if (!quoted) return sock.sendMessage(from, { text: ".vv reply view once message" }, { quoted: msg });

        const mimeType = Object.keys(quoted.message)[0];
        const isImage = mimeType === 'imageMessage';
        const isVideo = mimeType === 'videoMessage';
        const isAudio = mimeType === 'audioMessage';

        if (!isImage && !isVideo && !isAudio) {
            return sock.sendMessage(from, { text: " Unsupported!" }, { quoted: msg });
        }

        const messageType = mimeType.split('Message')[0];
        const stream = await downloadContentFromMessage(quoted.message[mimeType], messageType);
        let buffer = Buffer.from([]);
        for await (const chunk of stream) {
            buffer = Buffer.concat([buffer, chunk]);
        }

        const caption = quoted.message[mimeType]?.caption || "";

        let viewOnceContent;
        if (isImage) {
            viewOnceContent = toViewOncePhoto(buffer, caption);
        } else if (isVideo) {
            viewOnceContent = toViewOnceVideo(buffer, caption);
        } else if (isAudio) {
            viewOnceContent = toViewOnceVoice(buffer);
        }

        await sock.sendMessage(from, viewOnceContent, { quoted: msg });

    } catch (err) {
        console.error("VV Command Error:", err);
        await sock.sendMessage(from, { text: "Error." });
    }
};
