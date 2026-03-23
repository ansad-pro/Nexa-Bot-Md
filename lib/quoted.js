// © 2026 arun•°Cumar. All Rights Reserved.
import fs from 'fs';
import { fileURLToPath } from 'url';

export const fquoted = {
    channel: {
        key: {
            fromMe: false,
            participant: "0@s.whatsapp.net",
            remoteJid: "27796262030@s.whatsapp.net"
        },
        message: {
            newsletterAdminInviteMessage: {
                newsletterJid: "0@newsletter",
                newsletterName: " X ",
                caption: "ASURA-MD WHATSAPP BOT",
                inviteExpiration: "0"
            }
        }
    }
};

const __filename = fileURLToPath(import.meta.url);

fs.watchFile(__filename, () => {
    fs.unwatchFile(__filename);
    console.log('\x1b[0;32m' + __filename + ' \x1b[1;32mupdated!\x1b[0m');
    
});
