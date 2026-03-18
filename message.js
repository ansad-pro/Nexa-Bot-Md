import path from "path";
import { pathToFileURL } from "url";
import fs from "fs";
import { getToggles } from "./lib/toggles.js";
import { parseMessage } from "./lib/msgHelper.js";
import { executeCommand } from "./lib/loader.js";
import config from "./config.js";

export default async (sock, chatUpdate) => {
try {
const msg = chatUpdate.messages?.[0];
if (!msg || !msg.message || msg.key.remoteJid === "status@broadcast") return;

    const from = msg.key.remoteJid;    
    const sender = msg.key.participant || msg.key.remoteJid;    
    const isOwner = config.OWNER_NUMBER.includes(sender.split('@')[0]) || msg.key.fromMe;

   // mention sticker
    const mentions = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid || [];
 if (mentions.length > 5) {
    const stickerPath = './media/sticker.webp';
 if (fs.existsSync(stickerPath)) {
       await sock.sendMessage(from, {
       sticker: fs.readFileSync(stickerPath)
     }, { quoted: msg });
     return;
    }
  }

   // Parse Message    
    const { isCmd, commandName, args } = parseMessage(msg);    

    if (!isCmd || !commandName) return;    

    // Get Toggles   
    const toggles = getToggles();    

    // Command OFF check   
    if (toggles[commandName]?.status === "off") return;    

    // Global Private Mode Check   
    if (global.isPublic === false && !msg.key.fromMe) return;  

    //  Specific Command Private Check   
    if (toggles[commandName]?.mode === "private" && !msg.key.fromMe) {  
        return await sock.sendMessage(from, { text: "🔒 owner only." });  
    }  

    //  Execute Command  
   await executeCommand(commandName, sock, msg, args, { toggles, isOwner });

} catch (err) {    
    console.error("❌ Message Error:", err);    
  }
};
