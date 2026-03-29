import axios from 'axios';

export async function ytPlay(query) {
    const apis = [
        `https://api-faa.my.id/faa/ytplay?query=${query}`,
        `https://api.giftedtech.my.id/api/search/ytplay?query=${query}`,
        `https://api.botcahx.eu.org/api/search/ytplay?query=${query}&apikey=your_key`,
        `https://api.dreaded.site/api/youtube/play?query=${query}`
    ];

    for (let api of apis) {
        try {
            const { data } = await axios.get(api);

            if (data?.result) {
                return data.result;
            }

            if (data?.data) {
                return data.data;
            }

        } catch (e) {
            console.log("API Failed:", api);
        }
    }

    throw new Error("All Play APIs failed");
}
