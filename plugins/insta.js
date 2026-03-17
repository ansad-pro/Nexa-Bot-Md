import axios from 'axios';

export default async (sock, msg, args, extra) => {
    const chat = msg.key.remoteJid;
    const url = args.join(' ');
    
    if (!url) {
        return await sock.sendMessage(chat, {
            text: `❌ Provide Instagram URL\n\nUsage: *.insta* <instagram_url>\n\nExamples:\n.insta https://www.instagram.com/reel/C2RszEzplgq/\n.insta https://www.instagram.com/p/ABC123/`
        }, { quoted: msg });
    }
    
    if (!url.includes('instagram.com')) {
        return await sock.sendMessage(chat, {
            text: '❌ Invalid Instagram URL. Must be from instagram.com'
        }, { quoted: msg });
    }
    
    await sock.sendMessage(chat, { react: { text: '📥', key: msg.key } });
    
    try {
        const apiUrl = `https://api.sparky.biz.id/api/downloader/igdl?url=${encodeURIComponent(url)}`;
        const response = await axios.get(apiUrl, { timeout: 15000 });
        
        if (!response.data.status || !response.data.data || response.data.data.length === 0) {
            return await sock.sendMessage(chat, {
                text: '❌ Failed to download. The post may be:\n• Private\n• Deleted\n• Not available in your region'
            }, { quoted: msg });
        }
        
        const media = response.data.data[0];
        
        if (media.type === 'video') {
            await sock.sendMessage(chat, {
                video: { url: media.url },
                caption: '📥 *Instagram Reel/Video*\n\n> Downloaded by Nexa-Bot MD'
            }, { quoted: msg });
        } else if (media.type === 'image') {
            await sock.sendMessage(chat, {
                image: { url: media.url },
                caption: '📥 *Instagram Photo*\n\n> Downloaded by Nexa-Bot MD'
            }, { quoted: msg });
        } else {
            await sock.sendMessage(chat, {
                text: `📥 *Instagram Media*\n\nType: ${media.type}\nURL: ${media.url}`
            }, { quoted: msg });
        }
        
    } catch (e) {
        console.error('Instagram Downloader Error:', e.message);
        await sock.sendMessage(chat, {
            text: '❌ Download failed.\n\nPossible reasons:\n• URL is invalid\n• Content is private\n• Server is down\n\nTry again later!'
        }, { quoted: msg });
    }
};
