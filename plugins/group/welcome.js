import { toggleWelcome } from '../../lib/group.js';

export default {
    name: 'welcome',
    category: 'group',
    description: 'Turn welcome message on or off',
    async execute(sock, msg, args) {
        const groupJid = msg.key.remoteJid;

        if (!groupJid.endsWith('@g.us')) return;

        const action = args[0]?.toLowerCase();

        if (action === 'on') {
            toggleWelcome(groupJid, 'on');
            return sock.sendMessage(groupJid, { text: '✅ Welcome messages enabled for this group.' });
        } 
        
        if (action === 'off') {
            toggleWelcome(groupJid, 'off');
            return sock.sendMessage(groupJid, { text: '❌ Welcome messages disabled.' });
        }

        return sock.sendMessage(groupJid, { 
            text: 'Usage: *.welcome on* or *.welcome off*' 
        });
    }
};
