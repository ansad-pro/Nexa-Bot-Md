// © 2026 arun•°Cumar. All Rights Reserved.   
import { getQuoted } from './quoted.js'; 
import ownerHandler from '../plugins/owner.js';
import menuHandler from '../plugins/menu.js';  
import aliveHandler from '../plugins/alive.js';  
import pingHandler from '../plugins/ping.js';  
import urlHandler from '../plugins/url.js';  
import stickerHandler from '../plugins/sticker.js';  
  
export async function handleCommands(commandName, sock, msg, args, extra) {  
    const { isOwner, isAdmin } = extra;  
  
    //Get quoted 
    const quoted = getQuoted(msg);   
  
    // commands checking 
    switch (commandName) {
        case 'menu':
        case 'help':
            await menuHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        case 'owner':
            await ownerHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        case 'alive':
            await aliveHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        case 'ping':
            await pingHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        case 'url':
        case 'link':
            await urlHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        case 'sticker':
        case 's':
            await stickerHandler(sock, msg, args, { isOwner, isAdmin, quoted });
            break;

        default:
            console.log(`Unknown command: ${commandName}`);
            break;
    }
}
