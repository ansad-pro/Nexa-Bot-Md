import { downloadContentFromMessage } from '@whiskeysockets/baileys';

export const downloadViewOnceMedia = async (msg) => {
    const quoted = msg.message?.extendedTextMessage?.contextInfo;

    if (!quoted || !quoted.quotedMessage) {
        return null;
    }

    let qMsg = quoted.quotedMessage;

    // Resolve ViewOnce
    if (qMsg.viewOnceMessageV2) {
        qMsg = qMsg.viewOnceMessageV2.message;
    } else if (qMsg.viewOnceMessageV2Extension) {
        qMsg = qMsg.viewOnceMessageV2Extension.message;
    } else if (qMsg.viewOnceMessage) {
        qMsg = qMsg.viewOnceMessage.message;
    }

    const mType = Object.keys(qMsg)[0];
    const media = qMsg[mType];

    if (!['imageMessage', 'videoMessage', 'audioMessage'].includes(mType)) {
        return null;
    }

    const mediaType = mType.replace('Message', '');
    const stream = await downloadContentFromMessage(media, mediaType);

    let buffer = Buffer.from([]);
    for await (const chunk of stream) {
        buffer = Buffer.concat([buffer, chunk]);
    }

    return {
        buffer,
        type: mediaType
    };
};

