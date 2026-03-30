import { kickAllUsers } from '../../lib/group.js';

export default {
    name: 'kickall',
    category: 'group',
    description: 'Removes every member from the group',
    async execute(sock, msg, args) {
        const groupJid = msg.key.remoteJid;

        // Ensure it's a group
        if (!groupJid.endsWith('@g.us')) {
            return sock.sendMessage(groupJid, { text: 'This command is group-only!' });
        }

        const botNumber = sock.user.id.split(':')[0] + '@s.whatsapp.net';

        await sock.sendMessage(groupJid, { text: 'Cleaning up the group... Goodbye everyone! 🧹' });
        const result = await kickAllUsers(sock, groupJid, botNumber);

        if (result.status) {
            console.log(`Successfully removed ${result.count} members.`);
        } else {
            await sock.sendMessage(groupJid, { text: `Error: ${result.error || 'Check bot admin status!'}` });
        }
    }
};
