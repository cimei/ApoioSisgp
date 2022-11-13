
--
-- PostgreSQL database
--

-- Dumped from database version 13.6

--
-- Name: Apoio; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA IF NOT EXISTS "Apoio";

ALTER SCHEMA "Apoio" OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: User; Type: TABLE; Schema: Apoio; Owner: postgres
--

CREATE TABLE "Apoio"."User" (
    id bigint NOT NULL,
    "userNome" character varying(150) NOT NULL,
    "userEmail" character varying(150) NOT NULL,
    password_hash character varying(128) NOT NULL,
    email_confirmation_sent_on timestamp(3) without time zone,
    email_confirmed boolean,
    email_confirmed_on timestamp(3) without time zone,
    registered_on timestamp(3) without time zone,
    last_logged_in timestamp(3) without time zone,
    current_logged_in timestamp(3) without time zone,
    "userAtivo" boolean,
    "avaliadorId" bigint
);

ALTER TABLE "Apoio"."User" OWNER TO postgres;
COMMENT ON TABLE "Apoio"."User" IS 'User';
COMMENT ON COLUMN "Apoio"."User".id IS 'id';
COMMENT ON COLUMN "Apoio"."User"."userNome" IS 'userNome';
COMMENT ON COLUMN "Apoio"."User"."userEmail" IS 'userEmail';
COMMENT ON COLUMN "Apoio"."User".password_hash IS 'password_hash';
COMMENT ON COLUMN "Apoio"."User".email_confirmation_sent_on IS 'email_confirmation_sent_on';
COMMENT ON COLUMN "Apoio"."User".email_confirmed IS 'email_confirmed';
COMMENT ON COLUMN "Apoio"."User".email_confirmed_on IS 'email_confirmed_on';
COMMENT ON COLUMN "Apoio"."User".registered_on IS 'registered_on';
COMMENT ON COLUMN "Apoio"."User".last_logged_in IS 'last_logged_in';
COMMENT ON COLUMN "Apoio"."User".current_logged_in IS 'current_logged_in';
COMMENT ON COLUMN "Apoio"."User"."userAtivo" IS 'userAtivo';
COMMENT ON COLUMN "Apoio"."User"."avaliadorId" IS 'avaliadorId';
CREATE SEQUENCE "Apoio"."User_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "Apoio"."User_id_seq" OWNER TO postgres;

ALTER SEQUENCE "Apoio"."User_id_seq" OWNED BY "Apoio"."User".id;

--
-- Name: log_auto; Type: TABLE; Schema: Apoio; Owner: postgres
--

CREATE TABLE "Apoio".log_auto (
    id bigint NOT NULL,
    data_hora timestamp(3) without time zone NOT NULL,
    user_id bigint NOT NULL,
    msg character varying(150) NOT NULL
);

ALTER TABLE "Apoio".log_auto OWNER TO postgres;

COMMENT ON TABLE "Apoio".log_auto IS 'log_auto';
COMMENT ON COLUMN "Apoio".log_auto.id IS 'log_auto.id';
COMMENT ON COLUMN "Apoio".log_auto.data_hora IS 'log_auto.data_hora';
COMMENT ON COLUMN "Apoio".log_auto.user_id IS 'log_auto.user_id';
COMMENT ON COLUMN "Apoio".log_auto.msg IS 'log_auto.msg';

--
-- Name: log_auto_id_seq; Type: SEQUENCE; Schema: Apoio; Owner: postgres
--

CREATE SEQUENCE "Apoio".log_auto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "Apoio".log_auto_id_seq OWNER TO postgres;

ALTER SEQUENCE "Apoio".log_auto_id_seq OWNED BY "Apoio".log_auto.id;

ALTER TABLE ONLY "Apoio"."User" ALTER COLUMN id SET DEFAULT nextval('"Apoio"."User_id_seq"'::regclass);

ALTER TABLE ONLY "Apoio".log_auto ALTER COLUMN id SET DEFAULT nextval('"Apoio".log_auto_id_seq'::regclass);

--
-- Name: Insert new User; Type: INSERT INTO; Schema: Apoio; Owner: postgres
-- Password from hash: 12345678
--

INSERT INTO "Apoio"."User"(
	"userNome", "userEmail", password_hash, email_confirmation_sent_on, email_confirmed, email_confirmed_on, registered_on, last_logged_in, current_logged_in, "userAtivo", "avaliadorId")
	VALUES ('Administrador', 'administrador@noreply.gov.br', 'pbkdf2:sha256:260000$xZjsC0ecrAl4IkmS$95528f1b348ec9f34d5e8be571b87bb5df94d88315f0f36302ba6059fb12d943', '1904-01-01 00:00:01', 'true', '1904-01-01 00:00:02', '1904-01-01 00:00:00', null, null, 'true', null);
