//kick
export const kickUser = async (sock, msg, participants) => {
    try {
        const groupJid = msg.key.remoteJid;
        
        const response = await sock.groupParticipantsUpdate(
            groupJid, 
            participants, 
            "remove" 
        );

        return { status: true, response };
    } catch (e) {
        console.error("Kick Logic Error:", e);
        return { status: false, error: e };
    }
};

// kickall
export const kickAllUsers = async (sock, groupJid, botNumber) => {
    try {
        const metadata = await sock.groupMetadata(groupJid);
        const participants = metadata.participants;
        
        // Filter out the bot's number
        const targets = participants
            .map(p => p.id)
            .filter(id => id !== botNumber);

        if (targets.length === 0) return { status: false, message: "No one to kick!" };

        // mass removal
        const response = await sock.groupParticipantsUpdate(
            groupJid, 
            targets, 
            "remove"
        );

        return { status: true, count: targets.length };
    } catch (e) {
        console.error("KickAll Logic Error:", e);
        return { status: false, error: e };
    }
};


// promote
export const promoteUser = async (sock, groupJid, participants) => {
    try {
        // groupParticipantsUpdate handles promote, demote, add, and remove
        const response = await sock.groupParticipantsUpdate(
            groupJid, 
            participants, 
            "promote" 
        );

        return { status: true, response };
    } catch (e) {
        console.error("Promote Logic Error:", e);
        return { status: false, error: e };
    }
};

// demote 
export const demoteUser = async (sock, groupJid, participants) => {
    try {
        const response = await sock.groupParticipantsUpdate(
            groupJid, 
            participants, 
            "demote" 
        );

        return { status: true, response };
    } catch (e) {
        console.error("Demote Logic Error:", e);
        return { status: false, error: e };
    }
};

// mute
export const setGroupMute = async (sock, jid, announce) => {
    try {
        
        const setting = announce ? 'announcement' : 'not_announcement';
        
        await sock.groupSettingUpdate(jid, setting);
        return { status: true };
    } catch (e) {
        console.error("Mute Logic Error:", e);
        return { status: false, error: e };
    }
};
