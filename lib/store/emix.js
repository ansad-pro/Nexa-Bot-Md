import { downloadContentFromMessage } from '@whiskeysockets/baileys';
import { Sticker, StickerTypes } from 'wa-sticker-formatter';

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

export const makeSticker = async (msg) => {

    const quoted = msg.message?.extendedTextMessage?.contextInfo?.quotedMessage;

    let mediaMessage =
        msg.message?.imageMessage ||
        msg.message?.videoMessage ||
        quoted?.imageMessage ||
        quoted?.videoMessage ||
        quoted?.documentWithCaptionMessage?.message?.videoMessage ||
        quoted?.documentWithCaptionMessage?.message?.imageMessage ||
        msg.message?.viewOnceMessageV2?.message?.imageMessage ||
        msg.message?.viewOnceMessageV2?.message?.videoMessage;

    if (!mediaMessage) return null;

    const isVideo =
        mediaMessage.mimetype?.includes('video');

    const downloadType = isVideo ? 'video' : 'image';

    const stream = await downloadContentFromMessage(mediaMessage, downloadType);
    let buffer = Buffer.from([]);

    for await (const chunk of stream) {
        buffer = Buffer.concat([buffer, chunk]);
    }

    const sticker = new Sticker(buffer, {
        pack: 'Nexa-Bot MD Pack',
        author: 'arun•°Cumar',
        type: StickerTypes.FULL,
        categories: ['🔥', '✨'],
        id: 'nexa_pro_sticker',
        quality: 30
    });

    return await sticker.toBuffer();
};
