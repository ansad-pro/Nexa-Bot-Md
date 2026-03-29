import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { tmpdir } from 'os';
import { randomBytes } from 'crypto';

export const downloadYt = async (url, type = 'video') => {
    const apis = [
        `https://api-faa.my.id/faa/ytmp4?url=${url}`,
        `https://api.giftedtech.my.id/api/download/dlmp4?url=${url}`
    ];

    let downloadUrl = null;

    for (const api of apis) {
        try {
            const { data } = await axios.get(api);

            if (data?.result?.url) {
                downloadUrl = data.result.url;
                break;
            } else if (data?.url) {
                downloadUrl = data.url;
                break;
            }

        } catch (e) {
            console.log("API Failed:", api);
        }
    }

    if (!downloadUrl) throw new Error("All APIs failed");

    const fileName = `yt_${randomBytes(4).toString('hex')}.mp4`;
    const filePath = path.join(tmpdir(), fileName);

    const response = await axios({
        method: 'get',
        url: downloadUrl,
        responseType: 'stream'
    });

    const writer = fs.createWriteStream(filePath);
    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
        writer.on('finish', () => resolve(filePath));
        writer.on('error', reject);
    });
};
