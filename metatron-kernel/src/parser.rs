use std::error::Error;
use std::fmt;
use std::io::BufRead;

use serde_json::{Map, Value};

use crate::id::{DuplicateId, ExprId, IdTable, LevelId, NameId};
use crate::syntax::{Declaration, Expr, Level, Name};

#[derive(Clone, Debug)]
pub struct Meta {
    pub format_version: String,
    pub raw: Value,
}

#[derive(Clone, Debug)]
pub struct ParsedExport {
    pub meta: Meta,
    pub names: IdTable<NameId, Name>,
    pub levels: IdTable<LevelId, Level>,
    pub exprs: IdTable<ExprId, Expr>,
    pub declarations: Vec<Declaration>,
}

#[derive(Clone, Debug)]
pub struct ResolvedExport {
    pub meta: Meta,
    pub names: IdTable<NameId, Name>,
    pub levels: IdTable<LevelId, Level>,
    pub exprs: IdTable<ExprId, Expr>,
    pub declarations: Vec<Declaration>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ParseError {
    Io { line: usize, message: String },
    Json { line: usize, message: String },
    MissingMeta,
    UnsupportedFormat(String),
    Malformed { line: usize, message: String },
    Duplicate(DuplicateId),
    MissingName(NameId),
    MissingLevel(LevelId),
    MissingExpr(ExprId),
}

impl fmt::Display for ParseError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io { line, message } => write!(formatter, "I/O error at line {line}: {message}"),
            Self::Json { line, message } => {
                write!(formatter, "invalid JSON at line {line}: {message}")
            }
            Self::MissingMeta => write!(formatter, "first record must be format metadata"),
            Self::UnsupportedFormat(version) => {
                write!(formatter, "unsupported export format {version}")
            }
            Self::Malformed { line, message } => {
                write!(formatter, "malformed record at line {line}: {message}")
            }
            Self::Duplicate(error) => error.fmt(formatter),
            Self::MissingName(id) => write!(formatter, "missing name id {}", id.0),
            Self::MissingLevel(id) => write!(formatter, "missing level id {}", id.0),
            Self::MissingExpr(id) => write!(formatter, "missing expression id {}", id.0),
        }
    }
}

impl Error for ParseError {}

impl From<DuplicateId> for ParseError {
    fn from(error: DuplicateId) -> Self {
        Self::Duplicate(error)
    }
}

pub fn parse<R: BufRead>(reader: R) -> Result<ParsedExport, ParseError> {
    let mut lines = reader.lines().enumerate();
    let Some((_, first)) = lines.next() else {
        return Err(ParseError::MissingMeta);
    };
    let first = first.map_err(|error| ParseError::Io {
        line: 1,
        message: error.to_string(),
    })?;
    let meta_value = parse_json(&first, 1)?;
    let meta = parse_meta(meta_value)?;

    let mut export = ParsedExport {
        meta,
        names: IdTable::default(),
        levels: IdTable::default(),
        exprs: IdTable::default(),
        declarations: Vec::new(),
    };
    export.levels.insert(LevelId(0), Level::Zero)?;

    for (index, line) in lines {
        let line_number = index + 1;
        let line = line.map_err(|error| ParseError::Io {
            line: line_number,
            message: error.to_string(),
        })?;
        let value = parse_json(&line, line_number)?;
        parse_record(&mut export, value, line_number)?;
    }

    Ok(export)
}

impl ParsedExport {
    pub fn resolve(self) -> Result<ResolvedExport, ParseError> {
        for name in self.names.values() {
            let prefix = match name {
                Name::Str { prefix, .. } | Name::Num { prefix, .. } => *prefix,
            };
            require_name(&self.names, prefix)?;
        }

        for level in self.levels.values() {
            match level {
                Level::Zero => {}
                Level::Succ(level) => require_level(&self.levels, *level)?,
                Level::Max(left, right) | Level::IMax(left, right) => {
                    require_level(&self.levels, *left)?;
                    require_level(&self.levels, *right)?;
                }
                Level::Param(name) => require_name(&self.names, *name)?,
            }
        }

        for expr in self.exprs.values() {
            resolve_expr(&self, expr)?;
        }
        for declaration in &self.declarations {
            resolve_declaration(&self, declaration)?;
        }

        Ok(ResolvedExport {
            meta: self.meta,
            names: self.names,
            levels: self.levels,
            exprs: self.exprs,
            declarations: self.declarations,
        })
    }
}

fn parse_json(line: &str, line_number: usize) -> Result<Value, ParseError> {
    serde_json::from_str(line).map_err(|error| ParseError::Json {
        line: line_number,
        message: error.to_string(),
    })
}

fn parse_meta(value: Value) -> Result<Meta, ParseError> {
    let Some(version) = value
        .get("meta")
        .and_then(|meta| meta.get("format"))
        .and_then(|format| format.get("version"))
        .and_then(Value::as_str)
    else {
        return Err(ParseError::MissingMeta);
    };
    if version != "3.1.0" {
        return Err(ParseError::UnsupportedFormat(version.to_owned()));
    }
    Ok(Meta {
        format_version: version.to_owned(),
        raw: value,
    })
}

fn parse_record(export: &mut ParsedExport, value: Value, line: usize) -> Result<(), ParseError> {
    let object = value
        .as_object()
        .ok_or_else(|| malformed(line, "record is not an object"))?;
    if object.contains_key("meta") {
        return Err(malformed(
            line,
            "metadata must occur exactly once and first",
        ));
    }
    if object.contains_key("in") {
        return parse_name(export, object, line);
    }
    if object.contains_key("il") {
        return parse_level(export, object, line);
    }
    if object.contains_key("ie") {
        return parse_expr(export, object, line);
    }
    if let Some(value) = object.get("axiom") {
        export.declarations.push(parse_axiom(value, line)?);
        return Ok(());
    }
    if let Some(value) = object.get("def") {
        export.declarations.push(parse_definition(value, line)?);
        return Ok(());
    }
    if object.len() != 1 {
        return Err(malformed(line, "unknown structural record"));
    }
    let tag = object.keys().next().expect("length checked").clone();
    export.declarations.push(Declaration::Unsupported { tag });
    Ok(())
}

fn parse_name(
    export: &mut ParsedExport,
    object: &Map<String, Value>,
    line: usize,
) -> Result<(), ParseError> {
    let id = NameId(number(object, "in", line)?);
    let name = match (object.get("str"), object.get("num")) {
        (Some(value), None) => Name::Str {
            prefix: NameId(nested_number(value, "pre", line)?),
            value: nested_string(value, "str", line)?.to_owned(),
        },
        (None, Some(value)) => Name::Num {
            prefix: NameId(nested_number(value, "pre", line)?),
            value: nested_number(value, "i", line)?,
        },
        _ => return Err(malformed(line, "name must have exactly one of str or num")),
    };
    export.names.insert(id, name)?;
    Ok(())
}

fn parse_level(
    export: &mut ParsedExport,
    object: &Map<String, Value>,
    line: usize,
) -> Result<(), ParseError> {
    let id = LevelId(number(object, "il", line)?);
    let candidates = ["succ", "max", "imax", "param"]
        .into_iter()
        .filter(|key| object.contains_key(*key))
        .collect::<Vec<_>>();
    if candidates.len() != 1 {
        return Err(malformed(line, "level must have exactly one constructor"));
    }
    let level = match candidates[0] {
        "succ" => Level::Succ(LevelId(number(object, "succ", line)?)),
        "max" => {
            let (left, right) = pair(object, "max", line)?;
            Level::Max(LevelId(left), LevelId(right))
        }
        "imax" => {
            let (left, right) = pair(object, "imax", line)?;
            Level::IMax(LevelId(left), LevelId(right))
        }
        "param" => Level::Param(NameId(number(object, "param", line)?)),
        _ => unreachable!(),
    };
    export.levels.insert(id, level)?;
    Ok(())
}

fn parse_expr(
    export: &mut ParsedExport,
    object: &Map<String, Value>,
    line: usize,
) -> Result<(), ParseError> {
    let id = ExprId(number(object, "ie", line)?);
    let tags = ["bvar", "sort", "const", "app", "lam", "forallE", "letE"]
        .into_iter()
        .filter(|key| object.contains_key(*key))
        .collect::<Vec<_>>();
    if tags.len() != 1 {
        return Err(malformed(
            line,
            "expression must have exactly one constructor",
        ));
    }
    let expr = match tags[0] {
        "bvar" => Expr::BVar(number(object, "bvar", line)?),
        "sort" => Expr::Sort(LevelId(number(object, "sort", line)?)),
        "const" => {
            let value = object.get("const").expect("tag checked");
            Expr::Const {
                name: NameId(nested_number(value, "name", line)?),
                levels: nested_numbers(value, "us", line)?
                    .into_iter()
                    .map(LevelId)
                    .collect(),
            }
        }
        "app" => {
            let value = object.get("app").expect("tag checked");
            Expr::App {
                fun: ExprId(nested_number(value, "fn", line)?),
                arg: ExprId(nested_number(value, "arg", line)?),
            }
        }
        "lam" => binder_expr(object.get("lam").expect("tag checked"), line, true)?,
        "forallE" => binder_expr(object.get("forallE").expect("tag checked"), line, false)?,
        "letE" => {
            let value = object.get("letE").expect("tag checked");
            Expr::Let {
                ty: ExprId(nested_number(value, "type", line)?),
                value: ExprId(nested_number(value, "value", line)?),
                body: ExprId(nested_number(value, "body", line)?),
            }
        }
        _ => unreachable!(),
    };
    export.exprs.insert(id, expr)?;
    Ok(())
}

fn binder_expr(value: &Value, line: usize, lambda: bool) -> Result<Expr, ParseError> {
    let domain = ExprId(nested_number(value, "type", line)?);
    let body = ExprId(nested_number(value, "body", line)?);
    Ok(if lambda {
        Expr::Lam { domain, body }
    } else {
        Expr::Pi { domain, body }
    })
}

fn parse_axiom(value: &Value, line: usize) -> Result<Declaration, ParseError> {
    Ok(Declaration::Axiom {
        name: NameId(nested_number(value, "name", line)?),
        level_params: nested_numbers(value, "levelParams", line)?
            .into_iter()
            .map(NameId)
            .collect(),
        ty: ExprId(nested_number(value, "type", line)?),
    })
}

fn parse_definition(value: &Value, line: usize) -> Result<Declaration, ParseError> {
    let hints = value
        .get("hints")
        .ok_or_else(|| malformed(line, "definition is missing hints"))?;
    let reducible = hints.as_str() != Some("opaque");
    Ok(Declaration::Definition {
        name: NameId(nested_number(value, "name", line)?),
        level_params: nested_numbers(value, "levelParams", line)?
            .into_iter()
            .map(NameId)
            .collect(),
        ty: ExprId(nested_number(value, "type", line)?),
        value: ExprId(nested_number(value, "value", line)?),
        reducible,
    })
}

fn resolve_expr(export: &ParsedExport, expr: &Expr) -> Result<(), ParseError> {
    match expr {
        Expr::BVar(_) => Ok(()),
        Expr::Sort(level) => require_level(&export.levels, *level),
        Expr::Const { name, levels } => {
            require_name(&export.names, *name)?;
            for level in levels {
                require_level(&export.levels, *level)?;
            }
            Ok(())
        }
        Expr::App { fun, arg } => {
            require_expr(&export.exprs, *fun)?;
            require_expr(&export.exprs, *arg)
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            require_expr(&export.exprs, *domain)?;
            require_expr(&export.exprs, *body)
        }
        Expr::Let { ty, value, body } => {
            require_expr(&export.exprs, *ty)?;
            require_expr(&export.exprs, *value)?;
            require_expr(&export.exprs, *body)
        }
    }
}

fn resolve_declaration(export: &ParsedExport, declaration: &Declaration) -> Result<(), ParseError> {
    let (name, level_params, expressions): (NameId, &[NameId], &[ExprId]) = match declaration {
        Declaration::Axiom {
            name,
            level_params,
            ty,
        } => (*name, level_params, std::slice::from_ref(ty)),
        Declaration::Definition {
            name,
            level_params,
            ty,
            value,
            ..
        } => (*name, level_params, &[*ty, *value]),
        Declaration::Unsupported { .. } => return Ok(()),
    };
    require_name(&export.names, name)?;
    for parameter in level_params {
        require_name(&export.names, *parameter)?;
    }
    for expression in expressions {
        require_expr(&export.exprs, *expression)?;
    }
    Ok(())
}

fn require_name(names: &IdTable<NameId, Name>, id: NameId) -> Result<(), ParseError> {
    if id.0 == 0 || names.contains(id) {
        Ok(())
    } else {
        Err(ParseError::MissingName(id))
    }
}

fn require_level(levels: &IdTable<LevelId, Level>, id: LevelId) -> Result<(), ParseError> {
    levels
        .contains(id)
        .then_some(())
        .ok_or(ParseError::MissingLevel(id))
}

fn require_expr(exprs: &IdTable<ExprId, Expr>, id: ExprId) -> Result<(), ParseError> {
    exprs
        .contains(id)
        .then_some(())
        .ok_or(ParseError::MissingExpr(id))
}

fn number(object: &Map<String, Value>, key: &str, line: usize) -> Result<u64, ParseError> {
    object
        .get(key)
        .and_then(Value::as_u64)
        .ok_or_else(|| malformed(line, &format!("{key} must be an unsigned integer")))
}

fn nested_number(value: &Value, key: &str, line: usize) -> Result<u64, ParseError> {
    value
        .get(key)
        .and_then(Value::as_u64)
        .ok_or_else(|| malformed(line, &format!("{key} must be an unsigned integer")))
}

fn nested_string<'a>(value: &'a Value, key: &str, line: usize) -> Result<&'a str, ParseError> {
    value
        .get(key)
        .and_then(Value::as_str)
        .ok_or_else(|| malformed(line, &format!("{key} must be a string")))
}

fn nested_numbers(value: &Value, key: &str, line: usize) -> Result<Vec<u64>, ParseError> {
    value
        .get(key)
        .and_then(Value::as_array)
        .ok_or_else(|| malformed(line, &format!("{key} must be an array")))?
        .iter()
        .map(|value| {
            value
                .as_u64()
                .ok_or_else(|| malformed(line, &format!("{key} must contain unsigned integers")))
        })
        .collect()
}

fn pair(object: &Map<String, Value>, key: &str, line: usize) -> Result<(u64, u64), ParseError> {
    let values = object
        .get(key)
        .and_then(Value::as_array)
        .ok_or_else(|| malformed(line, &format!("{key} must be an array")))?;
    if values.len() != 2 {
        return Err(malformed(line, &format!("{key} must contain two levels")));
    }
    let left = values[0]
        .as_u64()
        .ok_or_else(|| malformed(line, &format!("{key} must contain unsigned integers")))?;
    let right = values[1]
        .as_u64()
        .ok_or_else(|| malformed(line, &format!("{key} must contain unsigned integers")))?;
    Ok((left, right))
}

fn malformed(line: usize, message: &str) -> ParseError {
    ParseError::Malformed {
        line,
        message: message.to_owned(),
    }
}
