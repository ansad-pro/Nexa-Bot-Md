export default async (sock, msg, args) => {
    const from = msg.key.remoteJid;

    // Check if the sender is the owner (only messages sent by you)
    if (!msg.key.fromMe) {
        return await sock.sendMessage(
            from,
            { text: "❌ This command can only be used by the owner!" },
            { quoted: msg }
        );
    }

    const newMode = args[0]?.toLowerCase();

    if (newMode === 'public') {
        global.isPublic = true;

        await sock.sendMessage(
            from,
            { text: "🔓 *Mode Changed:* Public\nNow everyone can use the bot." },
            { quoted: msg }
        );
    } 
    else if (newMode === 'private') {
        global.isPublic = false;

        await sock.sendMessage(
            from,
            { text: "🔒 *Mode Changed:* Private\nNow only the owner can use the bot." },
            { quoted: msg }
        );
    } 
    else {
        await sock.sendMessage(
            from,
            { text: "❓ *Usage:* .mode public | .mode private" },
            { quoted: msg }
        );
    }
};
