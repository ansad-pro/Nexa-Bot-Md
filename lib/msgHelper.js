import config from "../config.js";

export const parseMessage = (msg) => {
    const body = msg.message?.conversation || msg.message?.extendedTextMessage?.text || "";
    const text = body.trim();
    const isCmd = text.startsWith(config.PREFIX);
    const commandName = isCmd ? text.slice(config.PREFIX.length).split(" ")[0].toLowerCase() : "";
    const args = text.split(/ +/).slice(1);
    
    return { body, text, isCmd, commandName, args };
};
