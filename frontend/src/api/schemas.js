// ПОРОЖДЕННЫЙ ФАЙЛ. Не править руками.
export const schemas = {
    definitions: {
        Booking: {
            type: "object",
            properties: {
                id: { type: "string" },
                seat_id: { type: "string" },
                user_id: { type: "string" },
                starts_at: { type: "string" },
                ends_at: { type: "string" },
                status: { type: "string" }
            }
        },
        SeatListResponse: {
            type: "array",
            items: {
                type: "object",
                properties: {
                    id: { type: "string" },
                    code: { type: "string" }
                }
            }
        },
        TokenPair: {
            type: "object",
            properties: {
                access_token: { type: "string" },
                refresh_token: { type: "string" },
                expires_in: { type: "number" }
            }
        }
    },
    Booking: { $ref: "#/definitions/Booking" },
    SeatListResponse: { $ref: "#/definitions/SeatListResponse" },
    TokenPair: { $ref: "#/definitions/TokenPair" }
};